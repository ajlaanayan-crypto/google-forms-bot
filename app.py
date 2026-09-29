from flask import Flask, send_from_directory, request, jsonify
import threading
import time
import random
import os
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

app = Flask(__name__, static_folder='static')

# State variables
is_running = False
total_submissions = 0
current_name = "NONE"
countdown = 10
bot_thread = None
logs = ["System idle..."]

def add_log(msg):
    global logs
    logs.append(msg)
    if len(logs) > 50:
        logs = logs[-50:]

def bot_loop(url, names_list, areas_list, loop_names):
    global is_running, total_submissions, current_name, countdown
    
    original_names = list(names_list)
    original_areas = list(areas_list)
    
    with sync_playwright() as p:
        # Launch visible browser VERY FAST (no slow_mo)
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()
        
        while is_running:
            if not names_list or not areas_list:
                if loop_names:
                    add_log("List ended. Looping back...")
                    names_list = list(original_names)
                    areas_list = list(original_areas)
                else:
                    add_log("List completed. Sequence stopped.")
                    is_running = False
                    break
                    
            current_name = names_list.pop(0)
            current_area = random.choice(original_areas)
            
            # Countdown
            for i in range(10, 0, -1):
                if not is_running:
                    break
                countdown = i
                time.sleep(1)
                
            if not is_running:
                break
                
            countdown = 0
            add_log(f"Navigating to form for: {current_name}")
            
            try:
                # Need the viewform URL
                if url.endswith('formResponse'):
                    url = url.replace('formResponse', 'viewform')
                    
                page.goto(url, wait_until="load") # load is faster than networkidle
                time.sleep(1) # Short wait for DOM
                
                # Dynamic Form Filling (Works for ANY single-page form)
                # ONLY find listitems that contain a heading (i.e. actual Questions, NOT options)
                question_blocks = page.locator('div[role="listitem"]:has(div[role="heading"])').all()
                
                # Fallback if Google forms changes DOM
                if not question_blocks:
                    question_blocks = page.locator('div.geS5n').all()
                    
                text_index = 0
                
                add_log(f"Found {len(question_blocks)} questions. Filling FAST!")
                
                for i, block in enumerate(question_blocks):
                    if not is_running: break
                    
                    # Scroll to make it visible
                    block.scroll_into_view_if_needed()
                    time.sleep(0.1)
                    
                    # 1. Text Inputs (Ignore inputs inside 'Other' options which lack role=heading but we are already filtered!)
                    text_inputs = block.locator('input[type="text"], input.whsOnd.zHQkBf, textarea')
                    if text_inputs.count() > 0:
                        # Make sure it's not the "Other" text input
                        # "Other" inputs usually don't have aria-labelledby matching the question heading
                        if text_index == 0:
                            text_inputs.first.fill(current_name)
                            add_log(f"Filled Name: {current_name}")
                        elif text_index == 1:
                            text_inputs.first.fill(current_area)
                            add_log(f"Filled Area: {current_area}")
                        else:
                            text_inputs.first.fill("N/A")
                        text_index += 1
                        time.sleep(0.1)
                        continue
                        
                    # 2. Checkboxes
                    checkboxes = block.locator('div[role="checkbox"]')
                    if checkboxes.count() > 0:
                        all_cb = checkboxes.all()
                        count_to_check = random.randint(1, min(3, len(all_cb)))
                        chosen = random.sample(all_cb, count_to_check)
                        for cb in chosen:
                            cb.click() # Standard click
                            time.sleep(0.1)
                        add_log(f"Checked {count_to_check} boxes in question {i+1}")
                        continue
                        
                    # 3. Radio Buttons (includes Linear Scales)
                    radios = block.locator('div[role="radio"]')
                    if radios.count() > 0:
                        all_rad = radios.all()
                        chosen = random.choice(all_rad)
                        chosen.click() # Standard click
                        add_log(f"Selected radio in question {i+1}")
                        time.sleep(0.1)
                        continue
                        
                if not is_running: break
                
                # Submit
                time.sleep(0.5)
                submit_btns = page.locator('div[role="button"]:has-text("Submit")')
                if submit_btns.count() == 0:
                    submit_btns = page.locator('//span[normalize-space()="Submit"]')
                    
                if submit_btns.count() > 0:
                    submit_btns.first.scroll_into_view_if_needed()
                    time.sleep(0.2)
                    add_log("Clicking Submit FAST...")
                    submit_btns.first.click()
                    time.sleep(2) # Wait for submission success page
                    
                total_submissions += 1
                add_log("Status: SUCCESS")
                
            except Exception as e:
                add_log(f"Error during submission: {str(e)[:100]}")
            
        browser.close()
    is_running = False
    countdown = 10

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        "is_running": is_running,
        "total_submissions": total_submissions,
        "current_name": current_name,
        "countdown": countdown,
        "logs": logs
    })

@app.route('/api/start', methods=['POST'])
def start_bot():
    global is_running, bot_thread, logs, total_submissions
    
    if is_running:
        return jsonify({"success": False, "message": "Bot is already running."})
        
    data = request.json
    url = data.get('url', '').strip()
    names_text = data.get('names', '').strip()
    areas_text = data.get('areas', '').strip()
    loop_names = data.get('loop', False)
    
    if not url or not names_text or not areas_text:
        return jsonify({"success": False, "message": "URL, Names, and Areas are required."})
        
    # Split by comma or period (replaced by newline), preserve internal spaces
    names_list = [n.strip() for n in names_text.replace(',', '\n').replace('.', '\n').split('\n') if n.strip()]
    areas_list = [a.strip() for a in areas_text.replace(',', '\n').replace('.', '\n').split('\n') if a.strip()]
    
    if not names_list or not areas_list:
        return jsonify({"success": False, "message": "Name list or Area list is empty."})
        
    is_running = True
    logs = ["Sequence Initiated..."]
    bot_thread = threading.Thread(
        target=bot_loop, 
        args=(url, names_list, areas_list, loop_names),
        daemon=True
    )
    bot_thread.start()
    
    return jsonify({"success": True, "message": "Started."})

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    global is_running
    if is_running:
        is_running = False
        add_log("ABORT SIGNAL RECEIVED. Stopping...")
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5056, debug=False)
