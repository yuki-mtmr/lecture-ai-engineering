#APIのレート制限を行うプログラム
import time
import collections


class RateLimiter:
    def __init__(self, limit_per_minute):
        self.safety_count = 0 #安全のための緩和カウント時間
        self.limit_per_minute = limit_per_minute
        self.last_call_time = collections.deque()

    def __call__(self, func):
        #デコレータ用ラッパー
        def wrapper(*args, **kwargs):
            now = time.monotonic()

            #60秒以前の時間のキュー削除
            while self.last_call_time and self.last_call_time[0] <= now - 60:
                self.last_call_time.popleft()
            
            #1分間の呼び出し回数がレート超過の場合sleepさせる
            if len(self.last_call_time) >= self.limit_per_minute:
                #キューの一番古い呼び出しが期限切れになるまでの時間を計算しておく
                wait_time = self.last_call_time[0] + 60 - now
                print(wait_time)
                if wait_time > 0:
                    time.sleep(wait_time + self.safety_count)#リミッター本体
                    now = time.monotonic()#待機後に現在時刻更新
            #現在の呼び出し時刻をキューに追加
            self.last_call_time.append(now)

            #元の関数を実行して返す
            return func(*args, **kwargs)
        return wrapper

""" 
limiter = RateLimiter(20)

@limiter
def my_api_call(data):
    print(f"APIを呼び出しています: {data} at {time.time()}")
    # ここに実際のAPI呼び出しロジックを記述します
    return f"処理済み: {data}"


if __name__ == "__main__":
    print("レート制限のある処理のシミュレーションを開始します...")
    start_time = time.time()
    # 50回呼び出しを試みる
    for i in range(50):
        result = my_api_call(f"item_{i}")
        time.sleep(0.1) # 各呼び出しの間に少し処理時間をシミュレート

    end_time = time.time()
    print(f"\nシミュレーションが終了しました。合計所要時間: {end_time - start_time:.2f} 秒")
    print("1分あたり30回で50回の呼び出しを行う場合、最低でも約100秒かかります。") """
