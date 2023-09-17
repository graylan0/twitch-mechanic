# Twitch Mechanic
AI Mechanic Designed For Twitch Chatrooms



### Technologies

1. Twitchio
2. Openai
3. Fastapi
4. Uvicorn
   
## Setup


I created an install video going over the requirements. 
Below is the 4 minute long installation video for the program.
[![Install Video](https://img.youtube.com/vi/9umfIea238k/0.jpg)](https://www.youtube.com/watch?v=9umfIea238k)

(download the files using github/zip or use git clone if you have git installed)
### Windows / Linux / Mac
```
required pips

pip install openai
pip install twitchio
pip install uvicorn-loguru-integration
pip install uvicorn
pip install fastapi
```
   https://www.anaconda.com/download (anaconda dl)
   https://www.youtube.com/watch?v=YJC6ldI3hWk (how to install anacdona if you need it)
   https://www.youtube.com/watch?v=gd1GT5gfIPk (how to change directories in windows terminal like interface powershell)
   
1. Set up a virtual environment or install python natively (either way works) . Then navigate to the directoy storing the local code using the CD command (example cd C:\bot)  ( use the cd command ) 
   ```
   https://www.anaconda.com/download
   https://www.youtube.com/watch?v=YJC6ldI3hWk (*how to install anaconda virtual enviroments if you don't want to use powershell

   How to use CD with powershell to navigate directories https://www.youtube.com/watch?v=gd1GT5gfIPk
   download and install anaconda then open an anaconda terminal window with anaconda prompt
   ```

2. Install the package in editable mode with development dependencies:
   ```powershell
   pip install .
   ```
3. Edit the config.json and grab a twitch 0auth token as well as OpenaiAPI key using the processes below to fill in the config.json file:
   
   https://twitchtokengenerator.com/ get token here for the twitch configuration inside config.json

   https://platform.openai.com/account/api-keys get api keys for openai for the openai configuration inside config.json

   then put them inside the config.json.

   Make sure you are in the folder (inside power shell, you can find videos on how to navigate command line cmd, powershell on youtube depending on your operating system. For example, mac is fairly similar and also uses cd.

5. Run the executable:
   ```powershell
   
   twitch-plays-llm run


   ```



