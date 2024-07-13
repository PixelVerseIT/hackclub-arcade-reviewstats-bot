import asyncio
from playwright.async_api import async_playwright
from flask import Flask, jsonify

app = Flask(__name__)

async def get_rendered_content(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_load_state('networkidle')

        await page.wait_for_selector('text="Hours pending review"', timeout=10000)
        await page.wait_for_selector('text="Hours approved in past 7 days"', timeout=10000)

        visible_text = await page.evaluate('() => document.body.innerText')
        await browser.close()
        return visible_text

url = "https://airtable.com/appOKDJk2ALKSisEM/shriBhjoCj83rYCGT"

def parse_data(text):
    lines = text.split('\n')
    hours_pending = None
    hours_approved = None

    for i, line in enumerate(lines):
        if line.strip() == "Hours pending review":
            try:
                hours_pending = int(lines[i+2].strip())  
            except (IndexError, ValueError):
                print(f"Error parsing hours pending review. Line content: {lines[i+2] if i+2 < len(lines) else 'N/A'}")
        elif line.strip() == "Hours approved in past 7 days":
            try:
                hours_approved = int(lines[i+2].strip()) 
            except (IndexError, ValueError):
                print(f"Error parsing hours approved. Line content: {lines[i+2] if i+2 < len(lines) else 'N/A'}")

        if hours_pending is not None and hours_approved is not None:
            break

    return hours_pending, hours_approved

@app.route('/api/hours', methods=['GET'])
def get_hours():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                visible_text = loop.run_until_complete(get_rendered_content(url))

                print("Visible text content:")
                print(visible_text)

                hours_pending, hours_approved = parse_data(visible_text)

                if hours_pending is None or hours_approved is None:
                    return jsonify({"error": "Failed to extract data from the page", "content": visible_text}), 500

                return jsonify({
                    "hours_pending_review": hours_pending,
                    "hours_approved_past_7_days": hours_approved
                })
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)