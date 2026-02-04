from llm.gemini_llm import get_gemini_llm

def test_gemini():
    try:
        llm = get_gemini_llm()
        response = llm.invoke("explain about cat lifecycle")
        print(response)
    except Exception as e:
        print("Error occurred:", e)

if __name__ == "__main__":
    test_gemini()
