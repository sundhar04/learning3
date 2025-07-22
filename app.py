from flask import Flask
app= Flask(__name__)
@app.route('/',methods=['GET'])
def summ():
    a=20
    b=30
    c=-5
    sum=a+b+c
    return f"the total is{sum}"


if __name__ == "__main__":
    
    app.run(host="0.0.0.0",port=5000)
    
#docker build -t yourusername/yourimage:latest .
#docker push yourusername/yourimage:latest
