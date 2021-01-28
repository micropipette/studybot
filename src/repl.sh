# Run this on repl.it as your main.sh
while :
do
rm -rf studybot
git clone --branch main https://github.com/micropipette/studybot
cp -a studybot/src/. .
pip install -r requirements.txt
python main.py
done