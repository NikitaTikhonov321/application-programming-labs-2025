import argparse
import re


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str, help="Имя файла с исходными данными")
    parser.add_argument(
        "-o", "--output_file", type=str, required=True, help="Имя выходного файла"
    )
    return parser.parse_args()


def read_file(filename: str) -> str:
    """ 
    чтение содержимого файла
    """
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Файл '{filename}' не был найден")


def find_surname_and_phone(data: str) -> list[tuple[str, str]]:
    """ 
    создание шаблона и нахождение подходящих строк
    """
    pattern = r"Фамилия:\s*([^\n0-9]+)\s*(?:.*?\n)*?Номер телефона или email:\s*([\+\d\-\s\(\)]+)(?=\s*\n)"
    return re.findall(pattern, data, re.IGNORECASE)


def normalize_phone_number(phone_number: str) -> str:
    """ 
    нормировка номера телефона
    """
    phone_number = phone_number.strip()
    digits = re.sub(r"[^\d+]", "", phone_number)

    if digits.startswith("+7"):
        digits = "8" + digits[2:]
    elif not digits.startswith("8"):
        return ""

    digits = re.sub(r"\D", "", digits)

    if len(digits) == 11:
        return digits
    return ""


def prepare_result_lines(data: list[tuple[str, str]]) -> list[str]:
    """ 
    создание файла и запись подходящий фамилии и номера телефона
    """
    output = []
    for last_name, phone_number in data:
        norm_phone = normalize_phone_number(phone_number)
        if norm_phone:
            output.append(f"{last_name.strip()}: {norm_phone}")
    return output


def save_to_file(filename: str, lines: list[str]) -> None:
    """ 
    запись в файл фамилии и номер телефона
    """
    with open(filename, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


def main():
    try:
        args = parse_args()
        text = read_file(args.input_file)
        extracted = find_surname_and_phone(text)
        output_list = prepare_result_lines(extracted)
        save_to_file(args.output_file, output_list)
        print(f"Результат успешно сохранён в файл {args.output_file}")
    except Exception as ex:
        print("Ошибка: ", ex)

if __name__ == "__main__":
    main()
