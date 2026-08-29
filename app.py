import os
import io
import zipfile
from fastapi import FastAPI, Form, Request, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

import db
import qr_service

app = FastAPI(title="Smart QR Contact System")

# Initialize SQLite database
db.init_db()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Setup template engine and static files folder
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Helper: local host base URL (can be customized via environment variables in production)
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

# 1. Admin Dashboard Route
@app.get("/")
def admin_dashboard(request: Request):
    tags = db.get_all_tags()
    stats = db.get_stats()
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"tags": tags, "stats": stats}
    )

# 2. Batch Generate Tag IDs (Admin Action)
@app.post("/admin/generate")
def admin_generate(start_id: int = Form(...), count: int = Form(...)):
    if start_id < 1 or count < 1 or count > 100:
        raise HTTPException(status_code=400, detail="Invalid start ID or count (max 100).")
    
    generated_count = 0
    for i in range(start_id, start_id + count):
        tag_id = f"TAG{i:04d}"
        if db.create_tag(tag_id):
            generated_count += 1
            
    return RedirectResponse(url="/", status_code=303)

# 3. Dynamic QR URL Scanned by Phones
@app.get("/u/{tag_id}", response_class=HTMLResponse)
def view_tag(tag_id: str, request: Request):
    tag_id = tag_id.upper()
    profile = db.get_tag(tag_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Smart tag not found in system.")
        
    # If the tag is unclaimed -> Show Activation Screen
    if not profile.get("claimed"):
        return templates.TemplateResponse(
            request=request,
            name="activate.html",
            context={"tag_id": tag_id, "error": None}
        )
        
    # If claimed -> Increment Scan count and Show Public Profile Card
    db.increment_scan(tag_id)
    
    # Reload profile to show incremented stats
    profile = db.get_tag(tag_id)
    return templates.TemplateResponse(
        request=request,
        name="view.html",
        context={"profile": profile}
    )

# 4. Save Activation Profile (Claim Tag)
@app.post("/u/{tag_id}/activate")
def activate_tag(
    tag_id: str,
    request: Request,
    name: str = Form(...),
    title: str = Form(""),
    phone: str = Form(...),
    email: str = Form(""),
    whatsapp: str = Form(""),
    passcode: str = Form(...)
):
    tag_id = tag_id.upper()
    profile = db.get_tag(tag_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Tag not found.")
        
    if profile.get("claimed"):
        raise HTTPException(status_code=400, detail="Tag is already activated.")
        
    name = name.strip()
    phone = phone.strip()
    passcode = passcode.strip()
    
    if not name or not phone or not passcode:
        return templates.TemplateResponse(
            request=request,
            name="activate.html",
            context={"tag_id": tag_id, "error": "Name, Phone, and Passcode are required fields."}
        )
        
    db.claim_tag(
        tag_id=tag_id,
        name=name,
        title=title.strip(),
        phone=phone,
        email=email.strip(),
        whatsapp=whatsapp.strip(),
        passcode=passcode
    )
    
    return RedirectResponse(url=f"/u/{tag_id}", status_code=303)

# 5. Edit Profile Screen (Authentication + Edit Action)
@app.get("/u/{tag_id}/edit", response_class=HTMLResponse)
def edit_profile_page(tag_id: str, request: Request):
    tag_id = tag_id.upper()
    profile = db.get_tag(tag_id)
    
    if not profile or not profile.get("claimed"):
        raise HTTPException(status_code=404, detail="Activated tag profile not found.")
        
    return templates.TemplateResponse(
        request=request,
        name="edit.html",
        context={"tag_id": tag_id, "step": "auth", "error": None}
    )

@app.post("/u/{tag_id}/edit", response_class=HTMLResponse)
def edit_profile(
    tag_id: str,
    request: Request,
    passcode: str = Form(...),
    action: str = Form("verify"),
    name: str = Form(""),
    title: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    whatsapp: str = Form("")
):
    tag_id = tag_id.upper()
    profile = db.get_tag(tag_id)
    
    if not profile or not profile.get("claimed"):
        raise HTTPException(status_code=404, detail="Activated tag profile not found.")
        
    # Verify Passcode Security
    if not db.verify_passcode(tag_id, passcode):
        return templates.TemplateResponse(
            request=request,
            name="edit.html",
            context={"tag_id": tag_id, "step": "auth", "error": "Invalid passcode. Please try again."}
        )
        
    # If passcode is correct and action is SAVE
    if action == "save":
        name = name.strip()
        phone = phone.strip()
        
        if not name or not phone:
            return templates.TemplateResponse(
                request=request,
                name="edit.html",
                context={
                    "tag_id": tag_id,
                    "step": "edit",
                    "passcode": passcode,
                    "profile": profile,
                    "error": "Name and Phone fields are required."
                }
            )
            
        db.update_tag(
            tag_id=tag_id,
            name=name,
            title=title.strip(),
            phone=phone,
            email=email.strip(),
            whatsapp=whatsapp.strip()
        )
        return RedirectResponse(url=f"/u/{tag_id}", status_code=303)
        
    # Otherwise render the edit profile fields screen
    return templates.TemplateResponse(
        request=request,
        name="edit.html",
        context={
            "tag_id": tag_id,
            "step": "edit",
            "passcode": passcode,
            "profile": profile,
            "error": None
        }
    )

# 6. Generate contact vCard (.vcf) dynamically
@app.get("/u/{tag_id}/vcard")
def download_vcard(tag_id: str):
    tag_id = tag_id.upper()
    profile = db.get_tag(tag_id)
    
    if not profile or not profile.get("claimed"):
        raise HTTPException(status_code=404, detail="Profile not active.")
        
    vcard_lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"FN:{profile['name']}",
        f"N:{profile['name']};;;;",
        f"TITLE:{profile['title'] or ''}",
        f"TEL;TYPE=CELL:{profile['phone']}"
    ]
    
    if profile.get("email"):
        vcard_lines.append(f"EMAIL;TYPE=INTERNET:{profile['email']}")
        
    if profile.get("whatsapp"):
        # Format wa.me link as a social entry
        clean_wa = profile['whatsapp'].replace('+', '').replace(' ', '')
        vcard_lines.append(f"X-SOCIALPROFILE;TYPE=whatsapp:https://wa.me/{clean_wa}")
        
    vcard_lines.append("END:VCARD")
    vcard_content = "\n".join(vcard_lines)
    
    filename = f"{tag_id}_contact.vcf"
    return Response(
        content=vcard_content,
        media_type="text/vcard",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# 7. Real-time QR Code Live Preview API
@app.post("/api/qr/preview")
async def qr_preview(
    tag_id: str = Form(...),
    fg_color: str = Form("#000000"),
    bg_color: str = Form("#ffffff"),
    error_correction: str = Form("H"),
    logo: UploadFile = File(None)
):
    target_url = f"{BASE_URL}/u/{tag_id.upper()}"
    logo_bytes = None
    if logo and logo.filename:
        logo_bytes = await logo.read()
        
    qr_bytes = qr_service.generate_custom_qr(
        data=target_url,
        fg_color=fg_color,
        bg_color=bg_color,
        error_correction=error_correction,
        logo_bytes=logo_bytes
    )
    
    return Response(content=qr_bytes, media_type="image/png")

# 8. Single Customized QR Code Download Endpoint (POST, supporting logo uploads)
@app.post("/api/qr/download")
async def qr_download(
    tag_id: str = Form(...),
    fg_color: str = Form("#000000"),
    bg_color: str = Form("#ffffff"),
    error_correction: str = Form("H"),
    logo: UploadFile = File(None)
):
    tag_id = tag_id.upper()
    target_url = f"{BASE_URL}/u/{tag_id}"
    logo_bytes = None
    if logo and logo.filename:
        logo_bytes = await logo.read()
        
    qr_bytes = qr_service.generate_custom_qr(
        data=target_url,
        fg_color=fg_color,
        bg_color=bg_color,
        error_correction=error_correction,
        logo_bytes=logo_bytes
    )
    
    filename = f"{tag_id}_qr_custom.png"
    return Response(
        content=qr_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# 9. Simple Customized QR Code Download Endpoint (GET, no logo)
@app.get("/api/qr/download-simple")
def qr_download_simple(
    tag_id: str,
    fg_color: str = "#000000",
    bg_color: str = "#ffffff",
    ecc: str = "H"
):
    tag_id = tag_id.upper()
    target_url = f"{BASE_URL}/u/{tag_id}"
    
    qr_bytes = qr_service.generate_custom_qr(
        data=target_url,
        fg_color=fg_color,
        bg_color=bg_color,
        error_correction=ecc,
        logo_bytes=None
    )
    
    filename = f"{tag_id}_qr.png"
    return Response(
        content=qr_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# 10. Batch ZIP Export API (Downloads all active tag QRs configured with these colors)
@app.post("/admin/download-zip")
async def qr_download_batch_zip(
    fg_color: str = Form("#000000"),
    bg_color: str = Form("#ffffff"),
    error_correction: str = Form("H"),
    logo: UploadFile = File(None)
):
    tags = db.get_all_tags()
    if not tags:
        raise HTTPException(status_code=400, detail="No tags in the system to export.")
        
    logo_bytes = None
    if logo and logo.filename:
        logo_bytes = await logo.read()
        
    # Generate Zip in-memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for tag in tags:
            tag_id = tag["tag_id"]
            target_url = f"{BASE_URL}/u/{tag_id}"
            
            qr_bytes = qr_service.generate_custom_qr(
                data=target_url,
                fg_color=fg_color,
                bg_color=bg_color,
                error_correction=error_correction,
                logo_bytes=logo_bytes
            )
            
            # Put in zip file
            zip_file.writestr(f"{tag_id}_qr.png", qr_bytes)
            
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=smart_qr_tags_batch.zip"}
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)