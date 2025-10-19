from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def chatgpt_reallocation(prompt: str, headless: bool = False) -> str:
    """
    Opens ChatGPT in a Chrome browser, injects a multiline prompt safely,
    and returns the model's response. No login required.
    """
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1400,1000")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://chat.openai.com/")

    # Wait for the text area to load
    textarea = WebDriverWait(driver, 45).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#prompt-textarea > p"))
    )

    # Inject the text directly into the text area (prevents Enter key triggering)
    driver.execute_script("arguments[0].innerText = arguments[1];", textarea, prompt)

    # Find the parent form and submit using the Send button element
    send_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button[data-testid='send-button']")
        )
    )
    send_button.click()

    # Wait for model output to appear
    sleep(15)
    messages = driver.find_elements(By.CLASS_NAME, "markdown")
    response = messages[-1].text if messages else "No response captured."

    driver.quit()
    return response
