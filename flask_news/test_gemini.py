# from google import genai

# def test_gemini():
#     try:
#         client = genai.Client(api_key="AIzaSyC99Qd3bShD7d8ROWAv3rnkHD6iS2CgMnU")  # Replace with your actual key

#         response = client.models.generate_content(
#             model="models/gemini-1.5-pro",
#             contents="Hello Gemini! Say hi if you can hear me."
#         )

#         print("✅ Gemini Test Success:")
#         print(response.text)

#     except Exception as e:
#         print("❌ Gemini Test Failed:", e)

# if __name__ == "__main__":
#     test_gemini()

# from google import genai

# client = genai.Client(api_key="AIzaSyC99Qd3bShD7d8ROWAv3rnkHD6iS2CgMnU")

# print("Available Gemini models:")
# for m in client.models.list():
#     print("-", m.name)


from google import genai

def test_gemini():
    try:
        client = genai.Client(api_key="AIzaSyC99Qd3bShD7d8ROWAv3rnkHD6iS2CgMnU")  # keep your valid key

        response = client.models.generate_content(
            model="models/gemini-2.5-pro",   # ✅ latest working model
            contents="Hello Gemini! Say hi if you can hear me."
        )

        print("✅ Gemini Test Success:")
        print(response.text)

    except Exception as e:
        print("❌ Gemini Test Failed:", e)

if __name__ == "__main__":
    test_gemini()
