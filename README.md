# 🏰 Knowledge Dungeon 🏰

A gamified Q&A adventure built using `Streamlit`, `CrewAI`, and `LangChain` with a LLM-powered cast of agents guiding the player through trivia challenges. Players battle through levels, collect points, and survive with limited lives—all while being guided by a virtual narrator and hint system.

---

## 🚀 Features

- ✅ **Dynamic Question Generation** based on player level using LLMs.
- 🧠 **Semantic Answer Checking** using sentence embeddings (`MiniLM`) for flexible answer matching.
- 💡 **Hint System** for each question.
- 📜 **Narrator Agent** for immersive storytelling.
- 🎮 **Gamified Progression**: 10 levels, limited lives, and point tracking.
- 💾 **Persistent Question History** to avoid repetition across sessions.

---

## 🛠️ Tech Stack

- **[Streamlit](https://streamlit.io/)** – UI framework.
- **[LangChain](https://www.langchain.com/)** with **Groq** – LLM agent orchestration.
- **[CrewAI](https://github.com/joaomdmoura/crewai)** – Agent management.
- **[sentence-transformers](https://www.sbert.net/)** – Embedding-based answer validation.
- **LLM Used**: `meta-llama/llama-4-maverick-17b-128e-instruct` (via `ChatGroq`).

---

## 🎮 How to Play

1. Launch the app:
    ```bash
    streamlit run app.py
    ```

2. Read the narrator's introduction.

3. Answer general knowledge questions.
   - Use the **hint** if you're stuck (once per question).
   - Be careful—wrong answers cost a life!

4. Score points for each correct answer.
   - Every 3 correct answers = level up.
   - Reach Level 10 to win!

---

## 📁 File Overview

| File          | Purpose                              |
|---------------|--------------------------------------|
| `app.py`      | Main game logic                      |
| `history.txt` | Stores asked questions (avoid repeats) |
| `README.md`   | You are reading it 🙂                 |

---

## 🧠 Agents Breakdown

| Agent             | Role                                            |
|-------------------|-------------------------------------------------|
| `NarratorAgent`   | Welcomes the player with story context         |
| `QuestionAgent`   | Creates fresh, level-based trivia questions    |
| `HintAgent`       | Generates helpful but vague hints              |
| `AnswerCheckerAgent` | Validates answers with semantic comparison |

---

## 📦 Dependencies

Install with:

```bash
pip install streamlit langchain crewai sentence-transformers scikit-learn
