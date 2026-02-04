import cv2
import numpy as np


def detect_noise_in_frame(frame, method='gaussian', threshold=5, size=5):
    original = frame.copy()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    if method == 'median':
        filtered = cv2.medianBlur(gray, size)   # точечные шумы
    elif method == 'gaussian':
        filtered = cv2.GaussianBlur(gray, (size, size), 0)  # размытые шумы
    else:
        filtered = gray.copy()

    diff = cv2.absdiff(gray, filtered)
    _, noise_mask = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

    total_pixels = gray.shape[0] * gray.shape[1]
    noise_pixels = np.sum(noise_mask == 255)
    noise_level = (noise_pixels / total_pixels) * 100

    return noise_mask, noise_level


def analyze_video_noise(video_path, threshold=5, method='gaussian', size=5):
    noise_threshold = 1.5
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Не удалось открыть видео")
        return None

    # Получаем информацию о видео
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    video_info = {
        'fps': fps,
        'width': width,
        'height': height,
        'total_frames': total_frames
    }

    clean_frames = []
    noisy_frames = []
    noise_levels = []
    frame_count = 0

    print("🔍 Начинаем анализ видео...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break


        noise_mask, noise_level = detect_noise_in_frame(frame, method, threshold, size)
        noise_levels.append(noise_level)

        # Сохраняем информацию о кадре
        frame_data = {
            'frame_number': frame_count,
            'frame': frame.copy(),
            'noise_mask': noise_mask,
            'noise_level': noise_level,
            'timestamp': frame_count / fps
        }

        if noise_level > noise_threshold:
            noisy_frames.append(frame_data)
        else:
            clean_frames.append(frame_data)

        if frame_count % 10 == 0:
            print(f"Кадр {frame_count}, уровень шума: {noise_level:.2f}%")

        frame_count += 1

    cap.release()
    cv2.destroyAllWindows()

    print(f"Анализ завершен!")
    print(f"Чистых кадров: {len(clean_frames)}")
    print(f"Шумных кадров: {len(noisy_frames)}")
    print(f"Общий уровень шума: {np.mean(noise_levels):.2f}%")

    return clean_frames, noisy_frames, video_info



