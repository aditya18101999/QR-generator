# Smart Dynamic QR Code & Contact Management System

A production-ready, beautiful, and secure web application built with **FastAPI**, **SQLite**, and **Tailwind CSS** to generate, customize, and manage dynamic smart QR contact tags.

---

## 🌟 Key Features

*   **Dynamic Tag Routing**: Print a batch of blank physical QR tags (e.g. `TAG0001` to `TAG0010`) once. Scanners are prompted to claim and customize the tags, which can be updated digitally anytime.
*   **Premium Glassmorphic UI**: High-end Tailwind CSS interfaces with Google fonts (Outfit and Inter), vector icons, and smooth scale animations.
*   **Security Gating**: Secure claimed profile edits with a SHA-256 encrypted passcode setup during activation.
*   **Center Logo & Color Customizer**: Dynamic frontend color pickers and logo uploader. Automatically overlays and centers your brand logo over the QR code with forced High Error Correction (`ERROR_CORRECT_H`) to maintain scannability.
*   **One-Tap Contact Actions**:
    *   📞 **Call Directly**: Trigger phone dialing from the profile card.
    *   💬 **WhatsApp Message**: Instant pre-filled WhatsApp conversation link.
    *   ✉️ **Send Email**: Quick mailto link.
    *   👤 **Save Contact**: Dynamic **vCard (.vcf)** generation to download the contact details straight into the phone book.
*   **Admin Dashboard**: Monitor usage metrics (Total tags, claimed tags, total scan counts, and last scanned timestamps) and search tags instantly.
*   **Batch Export**: Download all generated tags in a single **ZIP archive**, pre-styled with your custom branding and colors.

---

## 🛠️ Technology Stack

*   **Backend**: Python, FastAPI, Uvicorn
*   **Database**: SQLite (with WAL mode enabled for concurrent read/write support)
*   **QR Processing**: `qrcode`, `Pillow` (Image manipulation)
*   **Frontend**: Jinja2 Templates, Tailwind CSS (via CDN), custom CSS / JS scripts, FontAwesome Icons

---

## 🚀 Getting Started (Local Setup)

### Prerequisites
*   Python 3.8+ installed on your machine.

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/aditya18101999/QR-generator.git
    cd QR-generator
    ```

2.  **Set up a Virtual Environment**:
    *   **Windows**:
        ```bash
        python -m venv .venv
        .venv\Scripts\activate
        ```
    *   **Mac/Linux**:
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Server**:
    ```bash
    python app.py
    ```

5.  **Access the System**:
    *   Open your browser and go to [http://localhost:8000/](http://localhost:8000/) to access the Admin Dashboard.
    *   Visit [http://localhost:8000/u/TAG0001](http://localhost:8000/u/TAG0001) to scan/activate individual tags.

---

## ☁️ Deployment & Online Hosting

This application is ready to be hosted online using cloud platforms like **Render** or **Railway**.

### Important: SQLite Persistence
Cloud hosting providers use ephemeral filesystems by default. To prevent your database of claimed tags from being deleted during restarts or code updates, you must:
1.  Attach a **Persistent Volume/Disk** (e.g. 1GB disk mounted at `/var/data`).
2.  Set the environment variable `DB_PATH` to `/var/data/tags.db` so database files write to the persistent volume.
3.  Set `BASE_URL` to your online website URL (e.g. `https://my-qr-app.onrender.com`) so the generated QR codes point to the online host instead of `localhost`.