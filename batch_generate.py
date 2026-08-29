import os
import qrcode

# Change this to your planned domain (e.g., https://mybrand.com/u/ or localhost for testing)
BASE_URL = "http://localhost:8000/u"

def generate_tag_batch(start_id: int, count: int, output_dir: str = "tags"):
    os.makedirs(output_dir, exist_ok=True)

    for i in range(start_id, start_id + count):
        tag_id = f"TAG{i:04d}"  # Creates TAG0001, TAG0002, etc.
        target_url = f"{BASE_URL}/{tag_id}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(target_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
        file_path = os.path.join(output_dir, f"{tag_id}.png")
        img.save(file_path)
        print(f"[+] Generated: {tag_id} -> {target_url}")

if __name__ == "__main__":
    # Generate first 10 sample sellable tags
    generate_tag_batch(start_id=1, count=10)
    print("\n[✓] All QR tags generated in the 'tags' folder!")