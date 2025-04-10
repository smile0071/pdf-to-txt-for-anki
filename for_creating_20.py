import fitz  # PyMuPDF
import os

def extract_highlighted_text(pdf_path, threshold=10):
    try:
        # Открытие PDF-документа
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Ошибка при открытии файла: {e}")
        return

    highlight_text = []  # Список для хранения выделенного текста
    seen_words = set()  # Множество для отслеживания уникальных слов (в нижнем регистре)
    total_word_count = 0  # Счетчик всех уникальных слов
    word_limit = 20  # Лимит для создания файла
    file_counter = 1  # Счетчик для уникальности имени файла

    # Папка для сохранения файлов
    output_folder = "words_from_highlights"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Функция группировки слов по расстоянию
    def group_words_by_proximity(words, threshold):
        groups = []
        current_group = [words[0]]
        for i in range(1, len(words)):
            prev_word = current_group[-1]
            curr_word = words[i]
            # Проверка расстояния между текущим и предыдущим словом
            if abs(curr_word[0] - prev_word[2]) < threshold:
                current_group.append(curr_word)
            else:
                groups.append(current_group)
                current_group = [curr_word]
        if current_group:
            groups.append(current_group)
        return groups

    # Обход всех страниц PDF
    for page_num, page in enumerate(doc, start=1):
        highlights = []  # Список для хранения координат выделений на странице

        # Обработка аннотаций на странице
        annot = page.first_annot
        while annot:
            if annot.type[0] == 8:  # Проверка на аннотацию выделения
                vertices = annot.vertices
                if len(vertices) == 4:  # Если выделение простое (прямоугольник)
                    highlights.append(fitz.Quad(vertices).rect)
                else:  # Если выделение многострочное
                    quads = [fitz.Quad(vertices[i:i+4]).rect for i in range(0, len(vertices), 4)]
                    highlights.extend(quads)
            annot = annot.next

        # Извлечение слов со страницы
        all_words = page.get_text("words")  # Список слов в формате (x0, y0, x1, y1, "слово", ...)

        # Получение текста из каждой области выделения
        for h in highlights:
            words_in_highlight = [w for w in all_words if fitz.Rect(w[:4]).intersects(h)]
            if words_in_highlight:
                grouped_words = group_words_by_proximity(words_in_highlight, threshold)
                for group in grouped_words:
                    sentence = " ".join([word[4] for word in group])
                    lower_sentence = sentence.lower()  # Приведение текста к нижнему регистру
                    if lower_sentence not in seen_words:  # Добавляем только уникальные группы
                        highlight_text.append(sentence)
                        seen_words.add(lower_sentence)
                        total_word_count += 1

                        # Если количество уникальных слов достигло лимита, сохранить в файл
                        if len(highlight_text) >= word_limit:
                            filename = os.path.join(output_folder, f"{file_counter}.txt")
                            with open(filename, "w", encoding="utf-8") as f:
                                f.write("\n".join(highlight_text))
                            print(f"Файл создан: {filename}")
                            highlight_text.clear()  # Очистка списка для следующего файла
                            file_counter += 1

    # Если остались слова в списке после обработки всех страниц, сохранить их в новый файл
    if highlight_text:
        filename = os.path.join(output_folder, f"highlighted_text_{file_counter}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(highlight_text))
        print(f"Файл создан: {filename}")

    # Вывод общего числа уникальных слов
    print(f"\nОбщее количество уникальных фрагментов в выделениях: {total_word_count}")

if __name__ == "__main__":
    # Запрашиваем путь к файлу у пользователя и используем raw строку для корректной обработки пути
    pdf_path = input("Enter PDF path: ").strip('"')
    # Если путь с одинарными обратными слешами, заменяем их на двойные
    pdf_path = pdf_path.replace("\\", "/")  # Заменяем все обратные слеши на прямые
    extract_highlighted_text(pdf_path)
