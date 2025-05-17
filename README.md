# transcribe-srt

`transcribe-srt` is a simple CLI tool that batches MP4 videos in a directory (or a single file), splits long audio into manageable chunks, and uses OpenAI’s Whisper API to generate timestamped SRT subtitle files. If a matching `.srt` already exists, it skips processing to avoid duplicates.

---

## 🔧 Requirements

- Python ≥ 3.13  
- [ffmpeg](https://ffmpeg.org/) / [ffprobe](https://ffmpeg.org/ffprobe.html) installed on your system  
- An OpenAI API key  
- [Poetry](https://python-poetry.org/) for dependency management

---

## ⚙️ Installation

1. Clone the repository:

```bash
   git clone https://github.com/miruohotspring/transcribe-srt.git
   cd transcribe-srt
```
 
2. Create a `.env` file in the project root:

```ini
OPENAI_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXXX
```

> **Note:**  Don’t commit your `.env` to version control.
 
4. Install dependencies with Poetry:

```bash
poetry install
```

---

## 🚀 Usage 

### Single-file mode 

```bash
poetry run gen-sub <INPUT_VIDEO.mp4> <OUTPUT.srt> [CHUNK_SECONDS]
```
 
- `<INPUT_VIDEO.mp4>` – path to one MP4 file
- `<OUTPUT.srt>` – destination SRT filename
- `[CHUNK_SECONDS]` – optional chunk length in seconds (default: 300)

**Examples:** 

```bash
poetry run gen-sub episode1.mp4 episode1.srt
poetry run gen-sub episode2.mp4 episode2.srt 180
```

### Directory-batch mode 

```bash
poetry run gen-sub <INPUT_DIR/> <OUTPUT_DIR/> [CHUNK_SECONDS]
```

- `<INPUT_DIR/>` – directory containing `.mp4` files
- `<OUTPUT_DIR/>` – where to write generated `.srt` files (created if missing)
- `[CHUNK_SECONDS]` – optional chunk length in seconds (default: 300)

Files are processed in sorted order; existing `.srt` files are skipped.

**Example:** 

```bash
poetry run gen-sub ./videos/ ./subtitles/ 120
```

---

## ⚠️ Notes 
 
- OpenAI API usage is **metered** . Check your account balance before batch-processing large video collections.
- The tool only supports MP4 inputs.

---

## 📄 License 

This project is released under the MIT License. See [LICENSE](https://chatgpt.com/c/LICENSE)  for details.
