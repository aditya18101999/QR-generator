import io
import qrcode
from PIL import Image

def generate_custom_qr(
    data: str,
    fg_color: str = "#0f172a",
    bg_color: str = "#ffffff",
    error_correction: str = "H",
    logo_bytes: bytes = None
) -> bytes:
    """
    Generates a QR code image as bytes.
    Supports foreground color, background color, error correction level,
    and a custom logo overlay in the center.
    """
    ecc_map = {
        "L": qrcode.constants.ERROR_CORRECT_L,
        "M": qrcode.constants.ERROR_CORRECT_M,
        "Q": qrcode.constants.ERROR_CORRECT_Q,
        "H": qrcode.constants.ERROR_CORRECT_H
    }
    ecc = ecc_map.get(error_correction.upper(), qrcode.constants.ERROR_CORRECT_H)
    
    # If there is a logo overlay, we force High error correction (H)
    # to guarantee the QR code is still readable despite the obstruction
    if logo_bytes:
        ecc = qrcode.constants.ERROR_CORRECT_H

    qr = qrcode.QRCode(
        version=None, # auto-detect version
        error_correction=ecc,
        box_size=10,
        border=4
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Generate Pillow image
    img = qr.make_image(fill_color=fg_color, back_color=bg_color).convert("RGBA")
    
    if logo_bytes:
        try:
            logo = Image.open(io.BytesIO(logo_bytes))
            # Calculate maximum size (up to 22% of QR width/height)
            qr_width, qr_height = img.size
            logo_max_size = int(qr_width * 0.22)
            logo.thumbnail((logo_max_size, logo_max_size))
            
            # Position at center
            logo_width, logo_height = logo.size
            pos = ((qr_width - logo_width) // 2, (qr_height - logo_height) // 2)
            
            # Paste logo, handling transparency
            if logo.mode in ("RGBA", "LA") or (logo.mode == "P" and "transparency" in logo.info):
                mask = logo.convert("RGBA").split()[3]
                img.paste(logo, pos, mask)
            else:
                img.paste(logo, pos)
        except Exception as e:
            # Gracefully log error but return the clean QR code without logo
            print(f"[-] Error applying logo to QR code: {e}")
            
    # Save the composite image to bytes
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
