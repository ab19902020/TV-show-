"""contact sheet of rendered stills: python3 contact.py out.jpg t1 t2 ..."""
import sys, cv2, numpy as np
out = sys.argv[1]; ts = sys.argv[2:]
ims = []
for t in ts:
    im = cv2.imread(f"build/stills/still_{t}.jpg")
    im = cv2.resize(im, (768, 432), interpolation=cv2.INTER_AREA)
    cv2.putText(im, t, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
    ims.append(im)
while len(ims) % 2: ims.append(np.zeros_like(ims[0]))
rows = [np.hstack(ims[i:i + 2]) for i in range(0, len(ims), 2)]
cv2.imwrite(out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
