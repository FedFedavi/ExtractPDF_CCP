import os
import json
import pdfplumber
import re
import csv
import tkinter as tk
from tkinter import filedialog, messagebox

# Файл с конфигурацией
CONFIG_FILE = "config.json"

# Загружаем настройки
def load_config():
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)

# Функция очистки текста
def limit_text(text, max_length=100):
    """Очищает текст от лишних разрывов строк, двойных пробелов и обрезает до max_length"""
    if not text:
        return "⚠ НЕ НАЙДЕНО"

    clean_text = re.sub(r"\s+", " ", text).strip()  # Удаляем лишние пробелы и переносы строк
    return clean_text[:max_length]  # Ограничиваем длину

# Функция объединения строк по `max_lines`
def merge_lines(text, max_lines):
    """Объединяет строки, чтобы данные не обрывались"""
    lines = text.split("\n")
    merged = []
    buffer = []

    for line in lines:
        if line.strip():
            buffer.append(line.strip())

        if len(buffer) >= max_lines or not line.strip():
            merged.append(" ".join(buffer))
            buffer = []

    if buffer:
        merged.append(" ".join(buffer))

    return "\n".join(merged)

# Функция извлечения данных
def extract_data_from_pdf(pdf_path, rules):
    data = {"Файл": os.path.basename(pdf_path)}

    with pdfplumber.open(pdf_path) as pdf:
        raw_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

    text_joined = " ".join(raw_text.split("\n"))  # Полный текст без переносов строк

    if config["enable_console_log"]:
        print(f"🔍 Обрабатываем: {pdf_path}")

    for rule in rules:
        max_lines = rule.get("max_lines", 0)
        search_text = merge_lines(raw_text, max_lines) if rule.get("join_lines", True) else raw_text
        matches = re.findall(rule["regex"], search_text, re.MULTILINE)

        if matches:
            extracted_text = limit_text(matches[0], 150 if "ФССП" in rule["name"] else 100)
            data[rule["name"]] = extracted_text
            if config["enable_console_log"]:
                print(f"✅ {rule['name']}: {extracted_text}")
        else:
            data[rule["name"]] = "⚠ НЕ НАЙДЕНО"
            if config["enable_console_log"]:
                print(f"❌ {rule['name']} не найдено.")

    return data

# Обработка всех PDF в папке
def process_pdfs_in_folder(folder_path, rules):
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
    results = []

    for pdf_file in pdf_files:
        pdf_path = os.path.join(folder_path, pdf_file)
        result = extract_data_from_pdf(pdf_path, rules)
        results.append(result)

    return results

# Функция для открытия файла
def open_file(path):
    if os.path.exists(path):
        os.startfile(path)
    else:
        messagebox.showerror("Ошибка", f"Файл не найден: {path}")

# Функция обработки файлов и сохранения CSV
def start_processing():
    folder_path = filedialog.askdirectory(title="Выберите папку с PDF")
    if not folder_path:
        return

    log_text.set("Обработка файлов...")
    root.update()

    # Загружаем шаблоны
    global config
    config = load_config()
    rules = config["rules"]

    results = process_pdfs_in_folder(folder_path, rules)

    if not results:
        log_text.set("❌ Нет PDF-файлов для обработки.")
        return

    # Сохраняем в CSV
    csv_path = os.path.join(folder_path, "результаты.csv")
    with open(csv_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    # Обновляем текст и делаем его кликабельным
    log_text.set(f"✅ Готово! CSV сохранен: {csv_path}")
    lbl_status.config(fg="blue", cursor="hand2")
    lbl_status.bind("<Button-1>", lambda e: open_file(csv_path))

    messagebox.showinfo("Обработка завершена", f"Файл сохранен:\n{csv_path}")

# Создаем GUI
root = tk.Tk()
root.title("Парсер PDF от приставов")
root.geometry("400x250")

log_text = tk.StringVar()
log_text.set("Выберите папку с PDF")

frame = tk.Frame(root)
frame.pack(pady=20)

btn_select_folder = tk.Button(frame, text="Выбрать папку", command=start_processing)
btn_select_folder.pack(pady=10)

lbl_status = tk.Label(root, textvariable=log_text)
lbl_status.pack()

btn_exit = tk.Button(root, text="Выход", command=root.quit)
btn_exit.pack(pady=10)

root.mainloop()
