from langchain_groq import ChatGroq, GroqEmbeddings
import streamlit as st
from crewai import Agent
import os
import time
import re
from difflib import SequenceMatcher
from sklearn.pairwise import cosine_similarity
# Initialize LLM
llm = ChatGroq(temperature=0, model_name="meta-llama/llama-4-maverick-17b-128e-instruct")

HISTORY_FILE = "history.txt"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return [line.strip() for line in f.readlines()]
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        for question in history:
            f.write(question + "\n")

# Session State Initialization
if "level" not in st.session_state:
    st.session_state.level = 1
    st.session_state.points = 0
    st.session_state.history = load_history()
    st.session_state.questions_answered = 0
    st.session_state.current_question = None
    st.session_state.hint = None
    st.session_state.hint_used = False
    st.session_state.lives = 3
    st.session_state.last_correct_answer = None

# Agents
class NarratorAgent(Agent):
    def act(self, level):
        return llm.invoke(
            f"Generate a short(2-3 lines at most) welcome message for the user like a narrator according to level, the user is at level:{level}"
        ).content.strip()

class QuestionAgent(Agent):
    def act(self, level, history):
        for _ in range(10):
            question = llm.invoke(
                f"Generate a general knowledge question for a Q and A game. The player is at level {level}. "
                f"Avoid repeating questions from this list: {history}. "
                f"Do not include MCQs, only a single general knowledge question."
                f"Don't show any helper messages or descriptions such as 'Here is a question for level x ' etc ."
            ).content.strip()
            if question and question not in history:
                return question
        return "No new questions available. Try again later."
        

class QuestionAgent(Agent):
    def act(self, level, history):
        for _ in range(10):
            question = llm.invoke(
                f"Generate a general knowledge question suitable for 5th to 8th grade students. The player is at level {level}. "
                f"Avoid repeating questions from this list: {history}. "
                f"Do not include MCQs, only a single general knowledge question."
                f"Don't show any helper messages or descriptions such as 'Here is a question for level x ' etc ."
            ).content.strip()
            if question and question not in history:
                return question
        return "No new questions available. Try again later."

class HintAgent(Agent):
    def act(self, level, question):
        return llm.invoke(f"Generate a hint for this question: {question}. The player is at level {level}, so don't reveal too much detail.").content

class AnswerCheckerAgent(Agent):
    def act(self, question, answer):
        return llm.invoke(
            f"Check if the user's answer: '{answer}' is correct for the question: '{question}'. Respond strictly with 'YES' or 'NO'."
        ).content.lower().strip()

    def reveal_answer(self, question):
        return llm.invoke(f"What is the correct answer to the question: '{question}'? Respond with just the answer.").content.strip()


class AnswerCheckerAgent(Agent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.embedder = GroqEmbeddings(model="nomic-embed-text-v1")

    def act(self, question, user_answer):
        correct = self.reveal_answer(question)
        return self.is_semantically_correct(user_answer, correct), correct

    def reveal_answer(self, question):
        return llm.invoke(f"What is the correct answer to the question: '{question}'? Respond with just the answer.").content.strip()

    def is_semantically_correct(self, user_answer, correct_answer):
        def normalize(text):
            return re.sub(r"[^\w\s]", "", text.lower())

        user_clean = normalize(user_answer)
        correct_clean = normalize(correct_answer)

        # Embed both
        user_embedding = self.embedder.embed_query(user_clean)
        correct_embedding = self.embedder.embed_query(correct_clean)

        # Cosine similarity
        sim = cosine_similarity([user_embedding], [correct_embedding])[0][0]
        return sim >= 0.80  # 80% similarity threshold

# Instantiate agents
narrator = NarratorAgent(role="Narrator", goal="Guide the story forward", backstory="Knows all details of the world and its characters.")
questioner = QuestionAgent(role="Questioner", goal="Generate a general knowledge question", backstory="Knows all general knowledge.")
hinter = HintAgent(role="Hinter", goal="Provide hints about the question", backstory="Knows the correct answer but gives limited hints.")
validator = AnswerCheckerAgent(role="Validator", goal="Check if the answer is correct", backstory="Knows the correct answer.")

# UI Setup
st.title("🏰 Knowledge Dungeon 🏰")
st.sidebar.header("📜 Game Stats")

# Hint Button
if st.sidebar.button("💡 Get Hint"):
    if not st.session_state.hint_used:
        st.info(f"💡 Hint: {st.session_state.hint}")
        st.session_state.hint_used = True
    else:
        st.sidebar.warning("You've already used the hint for this question.")

st.sidebar.write(f"**🏆 Level:** {st.session_state.level}")
st.sidebar.write(f"**💰 Points:** {st.session_state.points}")
st.sidebar.write(f"**❤️ Lives:** {st.session_state.lives}")

# Constants
MAX_LEVEL = 10
QUESTIONS_PER_LEVEL = 3
POINTS_PER_CORRECT = 10

def generate_new_question():
    question = questioner.act(st.session_state.level, st.session_state.history)

    if question != "No new questions available. Try again later.":
        st.session_state.current_question = question
        st.session_state.history.append(question)
        st.session_state.hint = hinter.act(st.session_state.level, question)
        st.session_state.hint_used = False
        save_history(st.session_state.history)
    else:
        st.session_state.current_question = "No more questions available!"

def main():
    level = st.session_state.level

    # Game completion logic
    if level > MAX_LEVEL or (level == MAX_LEVEL and st.session_state.questions_answered >= QUESTIONS_PER_LEVEL):
        st.success("🎉 Congratulations! You have won the game! 🎉")
        st.stop()

    # Game over logic
    if st.session_state.lives <= 0:
        st.error("💀 You have lost all your lives! Game Over!")
        st.write(f"Your score: {st.session_state.points}")
        if st.session_state.last_correct_answer:
            st.info(f"📘 The correct answer was: **{st.session_state.last_correct_answer}**")
        if st.button("Retry"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        st.stop()

    # Narrator Line
    st.write(f"📜 Narrator: {narrator.act(level)}")

    # Ask a new question
    if not st.session_state.current_question:
        generate_new_question()

    st.write(f"🔹 {st.session_state.current_question}")

    answer = st.text_input("Your Answer:")

    if st.button("Submit Answer"):
        if answer.strip():
            is_correct, correct_answer = validator.act(st.session_state.current_question, answer)

            if is_correct:
                st.success("✅ Correct! You defeated the enemy.")
                st.session_state.points += POINTS_PER_CORRECT
                st.session_state.questions_answered += 1
                time.sleep(1.5)

                if st.session_state.questions_answered >= QUESTIONS_PER_LEVEL:
                    if st.session_state.level < MAX_LEVEL:
                        st.session_state.level += 1
                        st.session_state.questions_answered = 0
                        st.success(f"🔺 Level Up! Welcome to Level {st.session_state.level}.")

                st.session_state.current_question = None
                st.rerun()
            else:
                st.error("❌ Wrong answer! Try again.")
                st.session_state.lives -= 1
                st.session_state.last_correct_answer = correct_answer
                time.sleep(1.5)
                st.rerun()

main()
