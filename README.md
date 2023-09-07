# Answer anything tool

## Description
This is a tool to answer anything you want to answer via BingAI, Google search with OpenAI. You can use it for building Chain-Of-Thought dataset to fine-tune your model.

## Requirement
First, please make sure you have Python version 3.6 or above (< 3.11) installed.
And install Cookie extension [1.11.0](https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm)
into your Browser (Recommend Edge).

Next, install the required packages using the command below:
```
pip install -r requirements.txt
```
P/S: Please use Conda for creating virtual environment and installing packages if you are using Windows.

## Usage

-------------------------
**I. Crawl data from BingAI**

-------------------------
Follow the steps below to use this tool:
1. Open your browser and login to your Bing account.
2. Go to [Bing](https://www.bing.com/) and search for anything you want to answer.
3. Open the Chat tab and wait for the bot to answer.
4. Click on the Cookie extension icon and export the cookie to a file (JSON format).
5. Copy that file to the "cookies" folder (inside the "tool" folder) and give it a name with format: "bing_cookie_{anything you want to write}.json".
6. Run the command below to start the tool:
```
python trial/playground.py
```
7. Rollback the Chat tab and type something to the bot. Then wait a minute for verification. And do step 4 to 5 again.
8. After the verification, the bot will start answering your question. You can stop the tool by pressing Ctrl + C.
9. After the crawling process, you can see a tab for visualizing the vectordb (all result will be saved in the "data" folder).

### Note
- The bot has a limit of 1000 answers per day. So please use it wisely. However, if you have the same question, you can query it in the vectordb without using the bot and I also implemented, you just need to call the "search" function of the "SearchEngine" class.
- You also can edit the prompt to make the bot answer more accurately.
- If you need to clean (not clear) the vectordb, remove some sub-pattern in the document, please run the command below:
```
python processing/clean_database.py
```

-------------------------
**II. Crawl data from ChatGPT**

-------------------------
No need custom anything, just call the class OpenGPTBot as you see in the "rewrite.py" file.

### Note
- **NOT** official ChatGPT, just a tool to crawl data from ChatGPT.
- **NOT** always work or response slowly, please use it wisely.

## Contact
If you have any questions, please contact me via email: [trinhhungsss492@gmail.com](mailto:trinhhungsss492@gmail.com)

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.