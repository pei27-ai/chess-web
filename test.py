# -*- coding: utf-8 -*-
"""
超级复杂太极八卦罗盘  ——  PyCharm 直接运行
纯标准库 tkinter，无需安装任何第三方包

快捷键：
    空格 / 鼠标左键   暂停 / 继续
    ↑ / ↓            加速 / 减速
    R                重置
"""

import math
import tkinter as tk

TAU = math.pi * 2

# ---------------- 配色 ----------------
BG       = "#060910"
GOLD     = "#d8b44a"
GOLD_LT  = "#e8c85a"
GOLD_DIM = "#8a6f2a"
JADE     = "#3fd0a8"
RED      = "#c0392b"
WHITE    = "#f5f1e6"
DARK     = "#0d1119"
LINE     = "#22304a"
LINE2    = "#1b2740"


class SuperBagua:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("超级太极八卦罗盘  |  空格暂停  ↑↓调速  R重置")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.W = self.H = 1000
        self.cx = self.W / 2.0
        self.cy = self.H / 2.0

        self.canvas = tk.Canvas(self.root, width=self.W, height=self.H,
                                bg=BG, highlightthickness=0)
        self.canvas.pack()

        self.paused = False
        self.speed_mul = 1.0

        # ---------------- 各层旋转角 ----------------
        self.a = {
            "taiji": 0.0,
            "bagua": 0.0,
            "gua64": 0.0,
            "term":  0.0,
            "gan":   0.0,
            "zhi":   0.0,
            "xiu":   0.0,
        }
        # ---------------- 各层基础角速度(弧度/帧) ----------------
        self.w = {
            "taiji":  0.0090,
            "bagua": -0.0055,
            "gua64":  0.0028,
            "term":  -0.0016,
            "gan":    0.0011,
            "zhi":   -0.0009,
            "xiu":    0.0006,
        }

        # ---------------- 半径参数 ----------------
        self.R_TAIJI   = 88.0
        self.R_BAGUA0  = 108.0      # 八卦最内爻
        self.D_BAGUA   = 20.0       # 爻间距
        self.R_BAGUA_N = 168.0      # 卦名半径
        self.R_64_0    = 186.0      # 64卦最内爻
        self.D_64      = 18.0       # 爻间距
        self.R_TERM    = 330.0      # 二十四节气文字
        self.R_GAN     = 372.0      # 天干
        self.R_ZHI     = 410.0      # 地支
        self.R_XIU_I   = 430.0      # 二十八宿刻度内
        self.R_XIU_O   = 444.0      # 二十八宿刻度外
        self.R_XIU_T   = 456.0      # 二十八宿文字
        self.R_TICK_I  = 468.0      # 外圈刻度内
        self.R_TICK_O  = 482.0      # 外圈刻度外

        # ---------------- 数据 ----------------
        # 先天八卦，自正上方顺时针；爻序「内 → 外」，1=阳 0=阴
        self.GUA = [
            ((1, 1, 1), "乾"),
            ((0, 1, 1), "巽"),
            ((0, 1, 0), "坎"),
            ((0, 0, 1), "艮"),
            ((0, 0, 0), "坤"),
            ((1, 0, 0), "震"),
            ((1, 0, 1), "离"),
            ((1, 1, 0), "兑"),
        ]

        self.TERMS = ["冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
                      "春分", "清明", "谷雨", "立夏", "小满", "芒种",
                      "夏至", "小暑", "大暑", "立秋", "处暑", "白露",
                      "秋分", "寒露", "霜降", "立冬", "小雪", "大雪"]

        self.GAN = list("甲乙丙丁戊己庚辛壬癸")
        self.ZHI = list("子丑寅卯辰巳午未申酉戌亥")
        self.XIU = ["角", "亢", "氐", "房", "心", "尾", "箕",
                    "斗", "牛", "女", "虚", "危", "室", "壁",
                    "奎", "娄", "胃", "昴", "毕", "觜", "参",
                    "井", "鬼", "柳", "星", "张", "翼", "轸"]

        # ---------------- 绑定 ----------------
        self.root.bind("<space>", self.toggle_pause)
        self.canvas.bind("<Button-1>", self.toggle_pause)
        self.root.bind("<Up>",   lambda e: self.change_speed(1.25))
        self.root.bind("<Down>", lambda e: self.change_speed(0.8))
        self.root.bind("<r>", self.reset)
        self.root.bind("<R>", self.reset)

        self.tick()
        self.root.mainloop()

    # ==================== 控制 ====================
    def toggle_pause(self, _=None):
        self.paused = not self.paused

    def change_speed(self, f):
        self.speed_mul = max(0.1, min(8.0, self.speed_mul * f))

    def reset(self, _=None):
        for k in self.a:
            self.a[k] = 0.0
        self.speed_mul = 1.0

    # ==================== 几何工具 ====================
    def pt(self, r, A):
        """极坐标 → 画布坐标；A=0 表示正上方，顺时针为正"""
        return (self.cx + r * math.sin(A),
                self.cy - r * math.cos(A))

    def yao_seg(self, r, A, u1, u2):
        """半径 r、方位 A 处，沿切向从 u1 到 u2 的线段两端点"""
        s, c = math.sin(A), math.cos(A)
        return ((self.cx + r * s + u1 * c, self.cy - r * c + u1 * s),
                (self.cx + r * s + u2 * c, self.cy - r * c + u2 * s))

    def draw_yao(self, r, A, half, gap, w, broken, color):
        """画一根爻"""
        if not broken:
            p1, p2 = self.yao_seg(r, A, -half, half)
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1],
                                    fill=color, width=w, capstyle=tk.ROUND)
        else:
            p1, p2 = self.yao_seg(r, A, -half, -gap)
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1],
                                    fill=color, width=w, capstyle=tk.ROUND)
            p1, p2 = self.yao_seg(r, A, gap, half)
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1],
                                    fill=color, width=w, capstyle=tk.ROUND)

    def ring(self, r, color, w=1, dash=None):
        self.canvas.create_oval(self.cx - r, self.cy - r,
                                self.cx + r, self.cy + r,
                                outline=color, width=w, dash=dash)

    # ==================== 中心太极 ====================
    def draw_taiji(self):
        R = self.R_TAIJI
        ang = self.a["taiji"]
        ca, sa = math.cos(ang), math.sin(ang)

        def P(x, y):
            return (self.cx + x * ca - y * sa,
                    self.cy + x * sa + y * ca)

        # 白色底盘
        self.canvas.create_oval(self.cx - R, self.cy - R,
                                self.cx + R, self.cy + R,
                                fill=WHITE, outline="")

        # 黑色阴鱼（S 形分界）
        N = 56
        pts = []
        for i in range(N + 1):                       # 上段：右凸弧 (0,-R) → (0,0)
            t = math.pi * i / N
            pts.append(P(R / 2 * math.sin(t), -R / 2 - R / 2 * math.cos(t)))
        for i in range(1, N + 1):                    # 下段：左凸弧 (0,0) → (0,R)
            t = math.pi * i / N
            pts.append(P(-R / 2 * math.sin(t), R / 2 - R / 2 * math.cos(t)))
        for i in range(1, N + 1):                    # 左半大圆 (0,R) → (0,-R)
            t = math.pi * i / N
            pts.append(P(-R * math.sin(t), R * math.cos(t)))

        flat = []
        for x, y in pts:
            flat.extend((x, y))
        self.canvas.create_polygon(*flat, fill=DARK, outline="")

        # 两条鱼眼
        er = R / 6.0
        ex, ey = P(0, -R / 2)
        self.canvas.create_oval(ex - er, ey - er, ex + er, ey + er,
                                fill=WHITE, outline="")
        ex, ey = P(0, R / 2)
        self.canvas.create_oval(ex - er, ey - er, ex + er, ey + er,
                                fill=DARK, outline="")

        # 金边
        self.ring(R, GOLD, 2.5)

    # ==================== 八卦层（三爻） ====================
    def draw_bagua(self):
        off = self.a["bagua"]
        r0 = self.R_BAGUA0
        d = self.D_BAGUA
        half, gap, w = 30.0, 9.0, 9

        for i, (yao, name) in enumerate(self.GUA):
            A = i * TAU / 8 + off
            for j, v in enumerate(yao):
                self.draw_yao(r0 + j * d, A, half, gap, w, v == 0, GOLD_LT)
            # 卦名
            tx, ty = self.pt(self.R_BAGUA_N, A)
            self.canvas.create_text(tx, ty, text=name, fill=JADE,
                                    font=("KaiTi", 15, "bold"))

    # ==================== 六十四卦层（六爻） ====================
    def draw_64(self):
        off = self.a["gua64"]
        r0 = self.R_64_0
        d = self.D_64
        w = 5

        for k in range(64):
            out_i = k // 8          # 上卦（外）
            in_i = k % 8            # 下卦（内）
            A = k * TAU / 64 + off

            # 六爻：内卦三爻 + 外卦三爻，由内向外
            seq = self.GUA[in_i][0] + self.GUA[out_i][0]

            for j, v in enumerate(seq):
                r = r0 + j * d
                half = r * 0.040          # 随半径放大，保持比例
                gap = half * 0.30
                col = GOLD_DIM if j < 3 else GOLD_LT
                self.draw_yao(r, A, half, gap, w, v == 0, col)

    # ==================== 二十四节气 ====================
    def draw_terms(self):
        off = self.a["term"]
        r = self.R_TERM
        for i, s in enumerate(self.TERMS):
            A = i * TAU / 24 + off
            p1 = self.pt(r - 14, A)
            p2 = self.pt(r - 4, A)
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1],
                                    fill=GOLD_DIM, width=1)
            x, y = self.pt(r, A)
            color = RED if i % 3 == 0 else "#9fb3c8"
            self.canvas.create_text(x, y, text=s, fill=color,
                                    font=("KaiTi", 13))

    # ==================== 天干 + 地支 ====================
    def draw_gan_zhi(self):
        off = self.a["gan"]
        for i, s in enumerate(self.GAN):
            A = i * TAU / 10 + off
            x, y = self.pt(self.R_GAN, A)
            self.canvas.create_text(x, y, text=s, fill="#d9a441",
                                    font=("KaiTi", 19, "bold"))

        off = self.a["zhi"]
        for i, s in enumerate(self.ZHI):
            A = i * TAU / 12 + off
            x, y = self.pt(self.R_ZHI, A)
            self.canvas.create_text(x, y, text=s, fill="#7fd6c0",
                                    font=("KaiTi", 17, "bold"))

    # ==================== 二十八宿 ====================
    def draw_xiu(self):
        off = self.a["xiu"]
        ri, ro, rt = self.R_XIU_I, self.R_XIU_O, self.R_XIU_T
        for i, s in enumerate(self.XIU):
            A = i * TAU / 28 + off
            p1 = self.pt(ri, A)
            p2 = self.pt(ro, A)
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1],
                                    fill="#3b6ea5", width=1.4)
            tx, ty = self.pt(rt, A)
            self.canvas.create_text(tx, ty, text=s, fill="#4a7fb5",
                                    font=("KaiTi", 11))

    # ==================== 外圈刻度 ====================
    def draw_ticks(self):
        ri, ro = self.R_TICK_I, self.R_TICK_O
        for i in range(120):
            A = i * TAU / 120
            if i % 10 == 0:
                p1, p2, w, col = self.pt(ri - 6, A), self.pt(ro, A), 2.0, GOLD
            elif i % 5 == 0:
                p1, p2, w, col = self.pt(ri, A), self.pt(ro - 3, A), 1.4, GOLD_DIM
            else:
                p1, p2, w, col = self.pt(ro - 8, A), self.pt(ro - 3, A), 1.0, "#33415a"
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1],
                                    fill=col, width=w)

    # ==================== 静态圆环 ====================
    def draw_static_rings(self):
        self.ring(98,  LINE, 1)
        self.ring(178, LINE, 1)
        self.ring(296, LINE2, 1)
        self.ring(314, LINE, 1)
        self.ring(348, LINE, 1)
        self.ring(390, LINE, 1)
        self.ring(428, LINE, 1)
        self.ring(488, LINE2, 1)

    # ==================== 主循环 ====================
    def tick(self):
        if not self.paused:
            for k in self.a:
                self.a[k] += self.w[k] * self.speed_mul
                if self.a[k] > TAU:
                    self.a[k] -= TAU
                elif self.a[k] < -TAU:
                    self.a[k] += TAU

        self.canvas.delete("all")

        self.draw_static_rings()
        self.draw_ticks()
        self.draw_xiu()
        self.draw_gan_zhi()
        self.draw_terms()
        self.draw_64()
        self.draw_bagua()
        self.draw_taiji()

        self.root.after(33, self.tick)


if __name__ == "__main__":
    SuperBagua()
