from flask import Flask, render_template, request, send_file
from playwright.sync_api import sync_playwright
import base64
import os
import webbrowser
from threading import Timer

app = Flask(__name__)

def get_image_base64(file):
    if file and file.filename != '':
        return base64.b64encode(file.read()).decode()
    return None

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/generate', methods=['POST'])
def generate_resume():
    try:
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        mobile = request.form.get('mobile', '')
        location = request.form.get('location', '')
        summary_h = request.form.get('summary_h', 'Summary')
        summary_t = request.form.get('summary_t', '')
        t_code = request.form.get('template', 't1')

        photo_file = request.files.get('photo')
        user_photo = get_image_base64(photo_file)

        contact_labels = request.form.getlist('contact_label[]')
        contact_values = request.form.getlist('contact_value[]')
        extra_contacts = [{"label": l, "value": v} for l, v in zip(contact_labels, contact_values) if l.strip()]

        headings = request.form.getlist('heading[]')
        details = request.form.getlist('details[]')
        custom_sections = [{"heading": h, "details": d} for h, d in zip(headings, details) if h.strip()]

        html_out = render_template(f'{t_code}.html',
                                   name=name,
                                   email=email,
                                   mobile=mobile,
                                   location=location,
                                   summary_h=summary_h,
                                   summary_t=summary_t,
                                   sections=custom_sections,
                                   photo=user_photo,
                                   extra_contacts=extra_contacts)
        
        # Temp HTML file likhna taaki playwright base64 photo ko bina block kiye pacha sake
        temp_html_path = os.path.join(os.getcwd(), "temp_resume.html")
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_out)
        
        pdf_name = f"{name}_Resume.pdf"
        pdf_path = os.path.join(os.getcwd(), pdf_name)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # File URL se kholne par photo turant load hoti hai
            page.goto("file:///" + temp_html_path.replace("\\", "/"))
            page.emulate_media(media="screen")
            page.pdf(path=pdf_path, format="A4", print_background=True, prefer_css_page_size=True)
            browser.close()
            
        # PDF banane ke baad temporary HTML file ko delete kar dena
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)
            
        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        return f"Error aaya hai: {str(e)}"

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
