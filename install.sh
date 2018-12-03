#for development mode

if [ "$(uname)" == "Darwin" ]; then
    echo 'darwin'
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    apt-get install libpython3-dev libssh-dev -y
fi
pip3 install -e .
