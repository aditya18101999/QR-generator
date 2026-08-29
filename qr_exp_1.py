import qrcode

def generate_qr(data: str, filename: str = "qrcode.png"):
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    print(f"\n[+] Success! QR code saved to: D:\\aiml\\qr-code-generator\\{filename}")

if __name__ == "__main__":
    user_text = input("Enter text or URL to encode: ").strip()
    if not user_text:
        user_text = "https://google.com"
    
    generate_qr(user_text, "my_qr_code.png")
