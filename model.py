import textwrap
import chromadb

import google.generativeai as genai
import google.ai.generativelanguage as glm

from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import MathpixPDFLoader
from langchain_community.document_loaders import UnstructuredPDFLoader

# from google.colab import userdata

from IPython.display import Markdown
from chromadb import Documents, EmbeddingFunction, Embeddings

class PDFChat_RAG:
    
    def __init__(self):
        self.document = None
        self.option = None
        self.retriever = None
        self.__API_KEY = 'AIzaSyCwu-pdy8MfRnCwJqkaAyXRA_zDzYxhQ60'
        self.db = None
        self.pages = None
        self.name = None

    def configure(self):
        genai.configure(api_key=self.__API_KEY)
    
    def parser(self, pdf_path):
        loader = PyPDFLoader(pdf_path)
        self.pages = loader.load_and_split()
    
    def create_chroma_db(self, name):
        embeddings = GoogleGenerativeAIEmbeddings(model='models/text-embedding-004',google_api_key=self.__API_KEY)
        self.db = Chroma.from_documents(self.pages, embeddings, collection_name = name)
    
    def q_and_a(self, context,input):
        prompt = """You are a helpful and informative bot that answers questions using text from the reference passage included below. \
        Be sure to respond in a complete sentence, being comprehensive, including all relevant background information. \
        However, you are talking to a non-technical audience, so be sure to break down complicated concepts and \
        strike a friendly and converstional tone. \
        If the passage is irrelevant to the answer, you may ignore it. \
        Also print the pages for citation, provided below and print only the numbers, avoid any associated characters \
        context: {context}
        input: {input}'

            ANSWER:
        """

        return prompt
    def summarize(self, context,input):

        prompt = """As a professional summarizer, create a concise and comprehensive summary of the provided text, be it an article, post, conversation, or passage, while adhering to these guidelines: \
        * Craft a summary that is detailed, thorough, in-depth, and complex, while maintaining clarity and conciseness. \
        * Incorporate main ideas and essential information, eliminating extraneous language and focusing on critical aspects. \
        * IMPORTANT: "If the given context is irrelevant to the answer, generate an answer based on the question given and kindly mention that this answer is not a part of the given text book". Otherwise, rely strictly on the provided context, without including external information. \
        * Format the summary in paragraph form for easy understanding.  \
        * Give a descriptive title \
        * Use bullet points if and only if there are any procedures or step by step information in the given passage. \
        context: {context}
        input: {input}        
        """

        return prompt
    
    def create_flashcards(self, context, input_text):
        prompt = f"""Based on the provided {context}, create flashcards with essential information and key points for easy memorization. Follow these guidelines:
        * Condense complex information into clear, concise points suitable for flashcards.
        * Focus on key concepts, definitions, and important details.
        * Use bullet points or lists for step-by-step processes or categorized information.
        * Include examples or mnemonics where helpful for better retention.
        * Keep each flashcard brief and to the point, emphasizing crucial information.
        * All points are to appear as separate paragraph
        context: {context}
        input: {input_text}
        """
        return prompt
    
    def create_quiz(self, context, input_text):
        prompt = f"""Design quiz questions and multiple-choice answers based on the provided {context}. Follow these guidelines:
        * Formulate clear and concise questions related to the topic.
        * Ensure each question has a correct answer and plausible distractors for multiple-choice options.
        * Use relevant terminology and concepts from the {context}.
        * Provide explanations for both correct and incorrect answers where necessary.
        * Include a variety of question types (e.g., multiple-choice, true/false, fill-in-the-blank) as appropriate.
        context: {context}
        input: {input_text}
        """
        return prompt
    
    # End point for getting PDF 
    def initialize_model(self, pdf_path, name):
        self.configure()
        self.parser(pdf_path)
        self.create_chroma_db(name)
        self.name = name

    # End point after receiving query from the user
    def run(self, option, query,pdfpath, name):
        # se
        self.configure()
        self.parser(pdfpath)
        self.create_chroma_db(name)
        
        retriever = self.db.as_retriever(search_kwargs={"k": 5})

        if option == 1:
            template = self.summarize(context="{context}", input="{input}")
        elif option == 2:
            template = self.q_and_a(context="{context}", input="{input}")
        elif option == 3:
            template = self.create_flashcards(context="{context}", input_text="{input}")
        elif option == 4:
            template = self.create_quiz(context="{context}", input_text="{input}")
        llm = ChatGoogleGenerativeAI(model="gemini-pro",google_api_key = self.__API_KEY)
        prompt = PromptTemplate.from_template(template)
        combine_docs_chain = create_stuff_documents_chain(llm, prompt)
        retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)

        #Invoke the retrieval chain
        response=retrieval_chain.invoke({"input":f"{query}"})
        result_pages = []
        for i in response['context']:
            if i.metadata['page'] > 10:
                result_pages.append(i.metadata['page'])

        #Print the answer to the question
        # Markdown(response['answer'])

        # Call a helper funtion to store the query, response to the database
        
        return result_pages, response['answer']

