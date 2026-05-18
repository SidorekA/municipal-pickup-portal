from playwright.sync_api import sync_playwright
import time

def verify():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width': 1280, 'height': 720}, record_video_dir=".")
        page = context.new_page()

        # Log in
        page.goto('http://127.0.0.1:8000/login/')
        page.fill('input[name="username"]', 'testuser')
        page.fill('input[name="password"]', 'password')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')

        # Take a screenshot to verify UI after our changes
        page.screenshot(path="verify_home.png")

        # Toggle sidebar a few times to show functionality
        page.click('button.btn-sidebar-toggle')
        time.sleep(1)
        page.click('button.btn-sidebar-toggle')
        time.sleep(1)

        # Ensure notification dropdown opens
        if page.locator('button.wf-notif-btn').is_visible():
            page.click('button.wf-notif-btn')
            time.sleep(1)

        context.close()
        browser.close()

if __name__ == "__main__":
    verify()
