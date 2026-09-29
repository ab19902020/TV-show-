"""Set definitions: plates, occluders (1x plate coords), seats (world px = 4x plate px)."""
import stage

# crimson executive boardroom at sunset: diagonal table, TV on the back wall
BOARD_OCC = [[(0, 548), (40, 543), (300, 548), (322, 562), (400, 553), (500, 528), (620, 489), (700, 462), (790, 438),
              (1040, 440), (1196, 452), (1206, 470), (1210, 941), (0, 941)]]

def boardroom():
    return stage.Stage("build/bg/boardroom_sunset.png", occluders=BOARD_OCC, ambient=(1.0, 0.97, 0.94),
                       rim=(-1.0, -0.4, 0.35, (1.0, 0.72, 0.45)), name="boardroom")
