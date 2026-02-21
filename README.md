# Video Editor
Приложение для обработки видео и фильтрации шумных кадров с использованием компьютерного зрения и PyQt6.

## Возможности

- **Анализ видео** на наличие шумных кадров
- **Два метода фильтрации**: Median и Gaussian
- **Визуализация результатов**: предпросмотр чистых и шумных кадров
- **Скачивание результатов**: сохранение обработанных видео

## Структура проекта
VideoEditor/
├── main.py              
├── gui.py               
├── video_processing.py 
├── requirements.txt  
├── Dockerfile         
└── README.md  

## Установка

### Способ 1: Локальная установка

1. Клонируйте репозиторий:
```bash
git clone https://git.miem.hse.ru/kg25-26/seabramova.git
cd VideoEditor
```

2. Создание и активация виртуального окружения:
```bash
python -m venv venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows
```

3. Активировать зависимости
```bash
pip install -r requirements.txt
```

3. Запуск
```bash
python app.py
```

### Способ 2: Запуск в Docker
На Windows/Mac для работы GUI понадобится X11 или VNC.
```bash
docker build -t video-editor .
docker run -it --rm     -e DISPLAY=$DISPLAY     -v /tmp/.X11-unix:/tmp/.X11-unix     video-
