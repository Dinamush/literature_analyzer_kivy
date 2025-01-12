import random
import openai
import os
import logging
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from dotenv import load_dotenv

# -------------------------------------------------------------
# Configure Logging
# -------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------
# Load environment variables from .env file
# -------------------------------------------------------------
load_dotenv()

# -------------------------------------------------------------
# 1. Define a helper class to interact with OpenAI's ChatCompletion
# -------------------------------------------------------------
class LiteracyAnalyzer:
    def __init__(self, api_key, model_name="gpt-4o"):
        self.api_key = api_key
        self.model_name = model_name
        logger.info("LiteracyAnalyzer initialized with model: %s", model_name)

    def analyze_literacy(self, user_answer: str) -> str:
        """
        Sends the user's answer to OpenAI's ChatCompletion
        and returns a response analyzing grammar, spelling, and vocabulary.
        """
        openai.api_key = self.api_key

        # Prompt design: The "system" role clarifies the assistant’s purpose.
        messages = [
            {
                "role": "system",
                "content": 
                    ( """
                You are an expert evaluator specializing in assessing the literacy level of user-submitted text. 
                Use the following criteria for your evaluation:

                1. Grammar and Syntax:
                - Assess correctness and complexity of sentence structures.
                - If the text is nearly error-free or accurate, assign a suitably high score.

                2. Spelling and Mechanics:
                - Evaluate spelling, punctuation, and capitalization.
                - Minor or infrequent errors should not drastically reduce the score.

                3. Vocabulary Usage:
                - Examine the range and appropriateness of vocabulary.
                - Avoid penalizing advanced or sophisticated word choice if it is accurate and contextually suitable.

                4. Cohesion and Coherence:
                - Check whether the text flows logically and remains easy to understand at a functional level.
                - Infrequent awkward transitions should not lower the score excessively if overall coherence is maintained.

                5. Organization and Structure:
                - Determine if the text includes a clear introduction, body, and conclusion (when relevant).
                - Consider how well the text serves its functional or communicative purpose.

                6. Content Relevance and Clarity:
                - Assess whether the content effectively conveys its intended message.
                - Avoid penalizing concise or precise writing if it meets the communicative goal.

                After analyzing the text against each criterion, provide:
                - A concise, constructive comment on each of the six criteria (in bullet points or short paragraphs).
                - An overall literacy rating (0 to 10) based on the following guidelines:
                • 0 indicates illiteracy.
                • 1–4 indicates very limited or poor literacy, requiring significant improvement.
                • 5–6 indicates basic functional literacy with areas still needing work.
                • 7–8 indicates generally proficient literacy with only minor improvements needed.
                • 9 indicates highly proficient literacy with minimal issues.
                • 10 indicates functional literacy at or near perfection for everyday needs.

                When in doubt—especially if the text is well-structured, precise, and exhibits minimal errors—err on the side of a higher rating. Provide short, constructive suggestions for improvement where applicable.
                """
                ),
            },
            {
                "role": "user",
                "content": f"User's text: {user_answer}",
            },
        ]

        try:
            logger.info("Sending request to OpenAI...")
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=messages,
                temperature=0,
                timeout=15,  # seconds
            )
            analysis = response["choices"][0]["message"]["content"].strip()
            logger.info("OpenAI response received successfully.")
            return analysis
        except openai.error.Timeout:
            logger.error("OpenAI API request timed out.")
            return "OpenAI API request timed out."
        except openai.error.APIError as e:
            logger.error("OpenAI API error: %s", e)
            return f"OpenAI API error: {e}"
        except openai.error.InvalidRequestError as e:
            logger.error("Invalid request to OpenAI API: %s", e)
            return f"Invalid request to OpenAI API: {e}"
        except Exception as e:
            logger.error("Unexpected error: %s", e)
            return f"Unexpected error: {e}"

# -------------------------------------------------------------
# 2. Kivy Screens
# -------------------------------------------------------------
class SplashScreen(Screen):
    """
    A simple splash screen that can show your logo.
    Transitions automatically to the main screen after a short delay.
    """

    def on_enter(self):
        """
        Overriding on_enter to ensure our transition method definitely runs.
        """
        logger.info("SplashScreen: on_enter event triggered.")
        # Schedule the transition
        self.transition_to_main()

    def transition_to_main(self):
        logger.info("Transition to main screen in 2 seconds...")
        Clock.schedule_once(self.go_to_main, 2)

    def go_to_main(self, dt):
        logger.info("Switching to main screen now.")
        # Defensive check: ensure 'main' screen actually exists
        if "main" in self.manager.screen_names:
            self.manager.current = "main"
        else:
            logger.warning("Main screen not found. Re-initializing ScreenManager with main.")
            # Fallback: Re-add or default to a known screen
            self.manager.current = "splash"  # Stay on splash or do something else


class MainScreen(Screen):
    """
    The main screen where questions are presented, the user can provide
    an answer, and then see the literacy analysis.
    """
    question_text = StringProperty("")
    analysis_result = StringProperty("")

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

        logger.info("MainScreen initializing...")

        self.questions = [
            "Describe your favorite book and why you like it.",
            "Explain how to bake a cake step by step.",
            "What does it mean to live a good life?",
            "Give your opinion on the importance of education.",
            "How would you teach someone to ride a bicycle?",
        ]
        # Retrieve the API key from environment variables
        api_key = os.getenv("API_KEY")
        logger.info("Loaded API_KEY: %s", api_key)

        if not api_key:
            raise ValueError("API_KEY not found in environment variables.")

        self.analyzer = LiteracyAnalyzer(
            api_key=api_key,
            model_name="gpt-4o-mini"
        )

    def on_enter(self, *args):
        """
        Called each time this screen is displayed. You can generate a question here.
        """
        logger.info("MainScreen entered.")
        self.generate_question()

    def generate_question(self):
        """
        Picks a random question from the list of questions.
        """
        question = random.choice(self.questions)
        logger.info("Generated question: %s", question)
        self.question_text = question

    def analyze_user_answer(self, user_answer: str):
        """
        Sends the user's answer to the OpenAI literacy analyzer
        and sets the result for display.
        """
        if not user_answer.strip():
            self.analysis_result = "Please enter an answer before analyzing."
            logger.warning("User did not enter an answer.")
            return

        logger.info("Analyzing user's answer: %s", user_answer)
        result = self.analyzer.analyze_literacy(user_answer)
        self.analysis_result = result
        logger.info("Analysis result: %s", result)

# -------------------------------------------------------------
# 3. Screen Manager
# -------------------------------------------------------------
class ScreenManagement(ScreenManager):
    pass

# -------------------------------------------------------------
# 4. Main App Class
# -------------------------------------------------------------
class LiteracyApp(App):
    def build(self):
        logger.info("Loading literacy_app.kv...")
        root_widget = Builder.load_file("literacy_app.kv")
        # Ensure that the default/current screen is splash
        root_widget.current = "splash"
        logger.info("Set ScreenManagement.current to 'splash'.")
        return root_widget

if __name__ == "__main__":
    LiteracyApp().run()
