from langchain_groq import ChatGroq
import streamlit as st
from crewai import Agent
import os
import time

# Initialize LLM
llm = ChatGroq(temperature=0.4, model_name="meta-llama/llama-4-maverick-17b-128e-instruct")

# File to store history
HISTORY_FILE = "history.txt"

# Load question history from file
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return [line.strip() for line in f.readlines()]
    return []

# Save question history to file
def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        for question in history:
            f.write(question + "\n")

# Initialize session state
if "level" not in st.session_state:
    st.session_state.level = 1
    st.session_state.points = 0
    st.session_state.history = load_history()  # Load history at startup
    st.session_state.questions_answered = 0
    st.session_state.current_question = None
    st.session_state.hint = None
    st.session_state.lives = 3

# Define Agents
class NarratorAgent(Agent):
    def act(self, level):
        return llm.invoke(f"Generate a short(2-3 lines at most) welcome message for the user like a narrator according to level, the user is at level:{level}").content.strip()

class QuestionAgent(Agent):
    def act(self, level, history):
        """Generate a unique question that is not in history"""
        for _ in range(10):  # Try multiple times to get a unique question
            question = llm.invoke(
                f"Generate a general knowledge question for a Q and A game. The player is at level {level}. "
                f"Avoid repeating questions from this list: {history}. "
                f"Do not include MCQs, only a single general knowledge question."
            ).content.strip()
            if question and question not in history:
                return question
        return "No new questions available. Try again later."

class HintAgent(Agent):
    def act(self, level, question):
        return llm.invoke(f"Generate a hint for this question: {question}. The player is at level {level}, so don't reveal too much detail.").content

class AnswerCheckerAgent(Agent):
    def act(self, question, answer):
        return llm.invoke(f"Check if the user's answer: '{answer}' is correct for the question: '{question}'. Only respond with 'yes' or 'no'.").content.lower().strip()

# Instantiate agents
narrator = NarratorAgent(role="Narrator", goal="Guide the story forward", backstory="Knows all details of the world and its characters.")
questioner = QuestionAgent(role="Questioner", goal="Generate a general knowledge question", backstory="Knows all general knowledge.")
hinter = HintAgent(role="Hinter", goal="Provide hints about the question", backstory="Knows the correct answer but gives limited hints.")
validator = AnswerCheckerAgent(role="Validator", goal="Check if the answer is correct", backstory="Knows the correct answer.")

# Streamlit App
st.title("🏰 Knowledge Dungeon 🏰")

# Sidebar for Level, Points & Lives Display
st.sidebar.header("📜 Game Stats")
st.sidebar.warning('Type "hint" to get hints from Gandalf ✨')

st.sidebar.write(f"**🏆 Level:** {st.session_state.level}")
st.sidebar.write(f"**💰 Points:** {st.session_state.points}")
st.sidebar.write(f"**❤️ Lives:** {st.session_state.lives}")

MAX_LEVEL = 10
QUESTIONS_PER_LEVEL = 3
POINTS_PER_CORRECT = 10

def generate_new_question():
    """Generates a unique new question and stores it in session state."""
    question = questioner.act(st.session_state.level, st.session_state.history)
    
    if question != "No new questions available. Try again later.":
        st.session_state.current_question = question
        st.session_state.history.append(question)
        st.session_state.hint = hinter.act(st.session_state.level, question)
        save_history(st.session_state.history)  # Save immediately to prevent duplicates
    else:
        st.session_state.current_question = "No more questions available!"

def main():
    level = st.session_state.level

    if level > MAX_LEVEL:
        st.success("🎉 Congratulations! You have won the game! 🎉")
        st.stop()
    
    if st.session_state.lives <= 0:
        st.error("💀 You have lost all your lives! Game Over!")
        st.write(f"Your score:{st.session_state.points}")
        if st.button("Retry"):
            del st.session_state.level
            st.rerun()
        st.stop()
        

    # Display Narration
    st.write(f"📜 Narrator: {narrator.act(level)}")

    # Generate a new question if needed
    if not st.session_state.current_question:
        generate_new_question()

    # Display the question
    st.write(f"**Sauron:** A feeble mortal dares to challenge me? Hah! Answer this question, or be doomed to eternal failure!")
    st.write(f"🔹 {st.session_state.current_question}")

    # User input
    answer = st.text_input("Your Answer:")

    if st.button("Submit Answer"):
        if answer.lower().strip() == "hint":
            st.info(f"💡 Hint: {st.session_state.hint}")
        elif answer.strip():
            response = validator.act(st.session_state.current_question, answer)
            if response in ['yes', 'yes.']:
                st.success("✅ Correct! You defeated the enemy.")
                st.session_state.points += POINTS_PER_CORRECT
                st.session_state.questions_answered += 1
                time.sleep(2)

                # Move to next level if necessary
                if st.session_state.questions_answered >= QUESTIONS_PER_LEVEL:
                    if st.session_state.level == MAX_LEVEL:
                        st.success("🎉 Congratulations! You have won the game! 🎉")
                        st.stop()
                    else:
                        st.session_state.level += 1
                        st.session_state.questions_answered = 0
                        st.success(f"🔺 Level Up! Welcome to Level {st.session_state.level}.")

                generate_new_question()
                st.rerun()
            else:
                st.error("❌ Wrong answer! Try again.")
                time.sleep(2)
                st.session_state.lives -= 1
                st.rerun()  # Force refresh to update lives in sidebar

main()
