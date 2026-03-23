import argparse
import re
import requests
import csv
from pathlib import Path

from bs4 import BeautifulSoup


def parse_arguments() -> argparse.Namespace:
    """
    Разбор и возврат аргументов командной строки.
    """

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-c", "--csv", dest="csv_file", type=str, default="out.csv", help="Название CSV файла"
    )
    parser.add_argument(
        "-d", "--dir", dest="directory", type=str, default="downloaded_mp3", help="Директория с файлами mp3"
    )

    return parser.parse_args()


def parse_html_content() -> BeautifulSoup | None:
    """
    Получение HTML-содержимого
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/58.0.3029.110 Safari/537.36"
        )
    }
    response = requests.get("https://mixkit.co/free-stock-music/pop/", headers=headers)
    if response.ok:
        return BeautifulSoup(response.text, "html.parser")
    return None


def write_file_paths_to_csv(file_paths: list[Path], filename: Path, out: Path) -> None:
    """
     Запись путей к файлам в CSV-файл.
    """

    with filename.open(mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["filename", "relative_path", "absolute_path"])
        for file_path in file_paths:
            absolute = file_path.resolve()
            relative = absolute.relative_to(Path.cwd())
            writer.writerow([file_path.name, str(relative), str(absolute)])


def extract_mp3_urls_from_html(soup: BeautifulSoup) -> list[Path]:
    """
     Извлечение URL-адресов MP3-файлов из JSON-LD скриптов в HTML-документе.
    """

    mp3_urls = []

    for script in soup.find_all("script", type="application/ld+json"):
        mp3_links = re.findall(r'"url"\s*:\s*"([^"]+\.mp3)"', script.string)
        for link in mp3_links:
            mp3_urls.append(link)

    return mp3_urls


class AudioFileIterator:
    """
    Итерируемый класс для обхода аудиофайлов из директории или CSV-файла.
    """

    def __init__(self, src: Path) -> None:
        """
        Инициализация итератора с указанием пути к источнику.
        """
        self.src = src
        self.file_paths: list[str] = []
        self.index = 0

        if self.src.is_dir():
            self.file_paths = sorted([f for f in self.src.glob("*.mp3") if f.is_file()])
        elif self.src.suffix == ".csv":
            self.load_from_csv(src)

    def __iter__(self) -> "IteratorFile":
        """
        Возвращает объект итератора.
        """
        self.index = 0
        return self

    def __next__(self) -> Path:
        """
        Возвращает следующий путь к файлу в итерации.
        """
        if self.index >= len(self.file_paths):
            raise StopIteration
        current = self.file_paths[self.index]
        self.index += 1
        return current

    def load_from_csv(self, filename: Path) -> None:
        """
        Загрузка путей к файлам из CSV-файла.
        """
        with filename.open("r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                absolute = row.get('absolute_path')
                if absolute:
                    self.file_paths.append(absolute)



def download_mp3_files() -> list[Path]:
    """
    Загрузка MP3-файлов с целевого веб-сайта и сохранение их локально.
    """

    files = []
    soup = parse_html_content()
    extracted = extract_mp3_urls_from_html(soup)
    mkdir_path = Path("downloaded_mp3")
    mkdir_path.mkdir(exist_ok=True)
    for link in extracted:
        filename = Path(link).name
        mp3_file = mkdir_path / filename
        responce = requests.get(link)
        with mp3_file.open("wb") as file:
            file.write(responce.content)
        files.append(mp3_file)
    return files


def main():
    try:
        args = parse_arguments()

        source = Path(args.csv_file)

        # Если CSV файл не существует или пуст, скачиваем файлы
        if not source.exists() or source.stat().st_size == 0:
            print("CSV файл не найден или пуст. Выполняется загрузка MP3 файлов...")
            downloaded_files = download_mp3_files()
            write_file_paths_to_csv(downloaded_files, source, Path(args.directory))

        iterator = AudioFileIterator(source)
        for item in iterator:
            print(item)

    except Exception as ex:
        print("Ошибка: ", ex)


if __name__ == "__main__":
    main()

