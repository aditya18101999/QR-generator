import urllib.request
import urllib.parse
import sys
import random

BASE_URL = "http://localhost:8000"

def run_test():
    print("[*] Starting programmatic verification of the FastAPI QR Contact System...")
    
    # Generate a random tag ID to ensure test runs are isolated and repeatable
    random_start = random.randint(1000, 9000)
    test_tag = f"TAG{random_start:04d}"
    print(f"[*] Isolated Test Tag for this run: {test_tag}")

    # 1. Test Dashboard Landing page
    try:
        response = urllib.request.urlopen(f"{BASE_URL}/")
        html = response.read().decode('utf-8')
        assert "Total Tags" in html, "Dashboard does not contain 'Total Tags'"
        assert "Active Smart Tags" in html, "Dashboard does not contain 'Active Smart Tags'"
        print("[PASS] Step 1: Dashboard page successfully loaded.")
    except Exception as e:
        print(f"[FAIL] Step 1 Failed: {e}")
        sys.exit(1)

    # 2. Test Batch Tag Generation
    try:
        data = urllib.parse.urlencode({
            "start_id": random_start,
            "count": 5
        }).encode('utf-8')
        req = urllib.request.Request(f"{BASE_URL}/admin/generate", data=data, method="POST")
        response = urllib.request.urlopen(req)
        # Check redirect or load
        html = response.read().decode('utf-8')
        assert test_tag in html, f"Generated tags table doesn't contain {test_tag}"
        print("[PASS] Step 2: Batch generation of tags succeeded.")
    except Exception as e:
        print(f"[FAIL] Step 2 Failed: {e}")
        sys.exit(1)

    # 3. Test Unactivated Tag Page (should show Activation Form)
    try:
        response = urllib.request.urlopen(f"{BASE_URL}/u/{test_tag}")
        html = response.read().decode('utf-8')
        assert "Activate Smart Tag" in html, "Unactivated tag page should show Activation Form"
        print("[PASS] Step 3: Unactivated tag page loaded correctly.")
    except Exception as e:
        print(f"[FAIL] Step 3 Failed: {e}")
        sys.exit(1)

    # 4. Test Profile Activation (Claim Tag)
    try:
        data = urllib.parse.urlencode({
            "name": "Jane Doe",
            "title": "Principal Architect",
            "phone": "+1234567890",
            "email": "jane@example.com",
            "whatsapp": "+1234567890",
            "passcode": "1234"
        }).encode('utf-8')
        req = urllib.request.Request(f"{BASE_URL}/u/{test_tag}/activate", data=data, method="POST")
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        assert "Jane Doe" in html, "Activated contact card does not display claimant name"
        assert "Principal Architect" in html, "Activated contact card does not display title"
        assert "Call Directly" in html, "Activated contact card does not contain Call button"
        print("[PASS] Step 4: Tag activation (claiming profile) succeeded.")
    except Exception as e:
        print(f"[FAIL] Step 4 Failed: {e}")
        sys.exit(1)

    # 5. Test Passcode Validation - Incorrect Passcode
    try:
        data = urllib.parse.urlencode({
            "passcode": "5555",
            "action": "verify"
        }).encode('utf-8')
        req = urllib.request.Request(f"{BASE_URL}/u/{test_tag}/edit", data=data, method="POST")
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        assert "Invalid passcode" in html, "Incorrect passcode did not display error message"
        print("[PASS] Step 5: Passcode verification correctly rejected incorrect passcode.")
    except Exception as e:
        print(f"[FAIL] Step 5 Failed: {e}")
        sys.exit(1)

    # 6. Test Passcode Validation - Correct Passcode (Load Form)
    try:
        data = urllib.parse.urlencode({
            "passcode": "1234",
            "action": "verify"
        }).encode('utf-8')
        req = urllib.request.Request(f"{BASE_URL}/u/{test_tag}/edit", data=data, method="POST")
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        assert "Update Your Profile" in html, "Correct passcode did not render edit form"
        print("[PASS] Step 6: Passcode verification succeeded and rendered edit profile page.")
    except Exception as e:
        print(f"[FAIL] Step 6 Failed: {e}")
        sys.exit(1)

    # 7. Test Save Profile Updates (Authorized)
    try:
        data = urllib.parse.urlencode({
            "passcode": "1234",
            "action": "save",
            "name": "Jane Doe",
            "title": "VP of Engineering",
            "phone": "+1234567890",
            "email": "jane@example.com",
            "whatsapp": "+1234567890"
        }).encode('utf-8')
        req = urllib.request.Request(f"{BASE_URL}/u/{test_tag}/edit", data=data, method="POST")
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        assert "VP of Engineering" in html, "Profile changes did not apply correctly"
        print("[PASS] Step 7: Profile editing and database updates succeeded.")
    except Exception as e:
        print(f"[FAIL] Step 7 Failed: {e}")
        sys.exit(1)

    # 8. Test QR Code Preview API
    try:
        data = urllib.parse.urlencode({
            "tag_id": test_tag,
            "fg_color": "#000000",
            "bg_color": "#ffffff",
            "error_correction": "H"
        }).encode('utf-8')
        req = urllib.request.Request(f"{BASE_URL}/api/qr/preview", data=data, method="POST")
        response = urllib.request.urlopen(req)
        
        # Query headers case-insensitively directly from the response info object
        content_type = response.info().get("content-type", "")
        assert "image/png" in content_type, f"QR preview API returned content-type '{content_type}', expected 'image/png'"
        
        qr_data = response.read()
        assert len(qr_data) > 100, "QR preview image size is too small (empty)"
        print("[PASS] Step 8: Dynamic QR Code Preview API succeeded.")
    except Exception as e:
        print(f"[FAIL] Step 8 Failed: {e}")
        sys.exit(1)

    print("\n[PASS] All verification tests passed successfully!")

if __name__ == "__main__":
    run_test()
