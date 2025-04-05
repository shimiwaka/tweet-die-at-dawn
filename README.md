# tweet-die-at-dawn
This repository is work in progress.

Post tweets that disappear after one hour

## Screenshot
![Sample Screenshot](sample.png)

## How to Run
1. Ensure you have Python 3 installed on your system.
2. Run the server using the command:
   ```
   python serve.py
   ```
3. Open your web browser and navigate to `http://localhost:8000` to access the tweet posting interface.

## Note
- Make sure the `send_tweet_command.dat` and `delete_tweet_command.dat` files are properly prepared.
- The server will automatically delete tweets after one hour using the `delete_tweet.rb` script.