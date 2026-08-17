# 1. Mãu lỗ lãi
=========================================================
- MAU_LAI_7_1  	: 7 điểm, vol T < T-1 (arg1)
- MAU_LAI_7_1_1	: MAU_LAI_7_1, biên độ T cao (arg2), Nến cắm hương giá đóng cửa gần sát với giá mở cửa và giá thấp nhất 
- MAU_LAI_7_1_2	: MAU_LAI_7_1, biên độ T cao (arg2), nến cover cả phiên T-1

- MAU_LAI_7_1_3	: MAU_LAI_7_1, biên độ T bình thường (arg2), nến T nằm sát đóng cửa T-1
- MAU_LAI_7_1_4	: MAU_LAI_7_1, biên độ T cao (arg2)

- MAU_LAI_7_2	: 7 điểm, vol T > T-1 (arg1)
- MAU_LAI_7_2_1	: MAU_LAI_7_2, xu hướng giảm giá và vol giảm dần qua các phiên, giá đóng cửa T nằm giữa mở cửa và đóng cửa T-1 còn giá mở cửa T < T-1 đóng cửa (ar2)

- MAU_LAI_7_4	: 7 điểm, T-1 là nến đỏ cover T-2 và vol < T-2, T thì là 1 cây nến xanh vol > T-1

- MAU_LAI_x_3  	: 1 xu hướng giảm vol tăng dần nhưng T-1 vol chững lại, vol T-1 > T
- MAU_LAI_x_4	: xu hướng giảm vol giảm dần, T nến xanh vol > T-1
=========================================================
- MAU_LO_7_1   	: 7 điểm, nến cắm hương giá đóng cửa sát gần với giá mở cửa, vol T >= 1.5 * vol T-1 (arg1)

- MAU_LO_7_2   	: 7 điểm, T-1 phiên giảm điểm lớn < -2.5% (arg1), Biến động giá T nhỏ (arg2) và giá đóng cửa gần mức thấp nhất, vol tương đương (ar3)
- MAU_LO_7_2_2 	: 7 điểm, T-1 phiên giảm điểm lớn < -2.5% (arg1), Biến động giá T nhỏ (arg2) và giá gần với mức cao nhất, vol tương đương(ar3)
- MAU_LO_7_2_4 	: 7 điểm, T-1 phiên giảm điểm lớn < -2.5% (arg1), Biến động giá T nhỏ (arg2) và giá gần với mức cao nhất, vol T nhỏ hơn rất nhiều T-1(ar3)

- MAU_LO_7_2_1 	: 7 điểm, T-1 phiên giảm điểm lớn < -2.5% (arg1), Biến động giá T lớn (arg2), vol T = 1.07 T-1 gần tương đương
- MAU_LO_7_2_3 	: 7 điểm, T-1 phiên giảm điểm lớn < -2.5% (arg1), Biến động giá T lớn (arg2) và giá gần với mức cao nhất, vol T nhỏ hơn rất nhiều T-1(ar3)
- MAU_LO_7_2_5 	: 7 điểm, T-1 phiên giảm điểm lớn < -2.5% (arg1), Biến động giá T lớn (arg2) và giá gần với mức cao nhất, vol T lớn hơn T-1(ar3)

- MAU_LO_7_2_6 	: 7 điểm, xu hướng giảm vol tăng dần sau đó là 1 phiên xanh T


- MAU_LO_7_3	: 7 điểm, T-2 nó là phiên mua trước tới nay là cổ về, biên độ giá nhỏ (arg1) giá đóng cửa ko vượt giá mở cửa của phiên đỏ T-1, vol T > T-1 (arg2)
- MAU_LO_7_3_1  : 7 điểm, T-2 nó là phiên mua trước tới nay là cổ về, biên độ giá lớn (arg1) giá đóng cửa ko vượt giá mở cửa của phiên đỏ T-1, vol T > T-1 (arg2)

- MAU_LO_7_4	: MAU_LAI_7_1, biên độ gần như Doji (arg2) nến T-1 cover nến T
- MAU_LO_7_4_1	: MAU_LAI_7_1, vol T vs T-1 -48%


- MAU_LO_7_5	: 7 điểm, mấy phiên gần nhất có giá đóng cửa thấp dần 

- MAU_LO_7_6	: 7 điểm, biên động T doji (arg1), vol T > T-1 (arg2)

- MAU_LO_7_7	: 7 điểm, vol T > T-1 (arg1)
- MAU_LO_7_7_1	: MAU_LO_7_7, Biên độ T lớn (arg2), giá đóng cửa T > giá mở cửa T-1

- MAU_LO_7_8	: MAU_LAI_7_1, giá T tăng nhiều(arg2)



- MAU_LAI_65_1	: 6.5 điểm, T-1 đỏ cover T-2, T-1 biên độ dao động lớn, T nến xanh lọt thỏm trong T-1 đỏ nhưng vol T = 1.4 T-1
- MAU_LO_65_1	: tương tự MAU_LO_7_1 nhưng 6.5 điểm

=========================================================
- MAU_HOA_7_1: 7 điểm, giá T so với T-1 >3% (arg1), vol T = 1.7 T-1 (arg2, PVC 20260708)

# 2. Mẫu holding
- MAU_HOLDING_1: nến đỏ nhưng có thể cover T-1 hoặc 1/2 T-1 nhưng vol lại rất nhỏ < trung bình

# 3. Mẫu bán
- MAU_BAN_X_1: chu kỳ tăng ,vol trong chu kỳ đó tăng giảm ko đồng đều. Nến phiên nay đỏ nằm sát giá đóng cửa của của T-1 ,vol > trung bình
- MAU_BAN_X_2: chu kỳ tăng, vol tăng đều nhưng T-1 mất đột ngột vol, T nến đỏ biên động giá cover T-1
- MAU_BAN_X_3: chu kỳ tăng, vol tăng đều nhưng T-1 vol > trung bình nhưng T nến đỏ < giá đóng cửa T-1 và vol < trung bình

# 20260508
- FPT: MAU_LAI_x_4
# 20260529
- FPT: MAU_LAI_7_1_3

# 20260604
- FPT: MAU_BAN_X_3


# 20260629
- PHR: 5 điểm, MAU_LAI_x_3 (40%)
 + Khi xanh ko bán, nhưng với phiên xanh mà vol cao kỷ lục > ma20 = 285% T-1 và 160% ma20
# 20260701
- NVL: MAU_LO_7_1,  volume T = 2.06*T-1 => -2.03%
- DGC: MAU_LO_7_2, (-2.51%), (+0.21%) => -0.42%
- GAS: MAU_LO_7_1, Vol = 1.44 * T-1 => -3.59%
- HSG:MAU_LO_7_3, biên độ giá rất nhỏ 0.43%,vol T  = 1.42 * T-1

#20260703
- PVC: MAU_LO_7_2, nến  T-1 đỏ đặc bao chùm lên nến xanh T-2, (-2.31%),  => Hồi ở phiên T và có thể giảm ở phiên tiếp theo, vol T > 1.1 T-1 => -0.47%
- NKG: tương tự PVC nhưng vol T >1.7 T-1 => 0%
===== BÁN======
- BSI: MAU_BAN_X_1

#20260702
- TPB: MAU_BAN_X_2

#20260706
- LPB: MAU_LAI_7_1_1, vol T so với T-1 = -13%  => 3.39%
- NVL: MAU_LO_65_1,  vol T = 2.88 T-1 => 2.37%

#20260707
- PET: MAU_LAI_7_1, nhưng biên động T-1 cao 9% giá đóng cửa sát với giá cao nhất tạo thành nến chân dài, vol T < -60% T-1 => 2.67%

#20260708
- THD: MAU_LAI_7_1_2 => 10.2%
- PVC: MAU_HOA_7_1 => 0.0%
- PLC: MAU_LAI_7_1_1 (1.95%), nhưng Giá T-1 (-2.38%) => 0.48%
- HPG: MAU_LO_7_4 () (0.22%, 0.43%) => -1.09%
- DDV: 6 điểm, xu hướng xuống mạnh mẽ vol tăng dần nhưng phiên T-1 chững lại, giá đóng gần như cover cả nến T-1 giá đóng cửa > giá mở cửa T-1 mà vol T < T-1 (phân kỳ chăng)=>2.86%
#20260713
- GEE: MAU_LO_7_6 (0.12%, 0.37%) => -0.5%
- CII: MAU_LO_7_1 (1.49%) => -2.53%
- VPL: MAU_LO_7_5 => 1.34%
- PVS: MAU_LO_65_2 => +2.63%

#20260714 <-25%
- PHR: MAU_LO_7_2_1 => -2.21%
- TRC: MAU_LO_7_2_2 (-3.19%) (H_L: 1.92%, C_O: 0.63%) (-15.34%)
- DPR: MAU_LO_7_4, T-1 giảm lớn (-1.82%), vol T vs T-1 (-23.35%) => -1.06%
- NVL: MAU_LAI_7_1 (0.41%, 0.41%) (-33.56%) => 3.56%
- DPG: MAU_LO_7_5 => -6.15%
- THD: MAU_LO_7_2_3 (-8.93%), (12.39%), (-60%) =>-7.96%
- NT2: MAU_LO_7_2_3 (-2.29%), (3.08%, 2.37%) (-9.19%) => -1.41%
- DGC: MAU_LO_7_4 (0.22%) => -1.34%
- DDV: MAU_LO_7_2_4 (-3.14%) (0.93%) (-57.33%) => -0.93%
- PAC: MAU_LO_7_5: -1.41%
- MSR: MAU_LAI_7_1 nhưng chân dài từ các phiên trước đó: -1.97%

#20260716
- FOC: MAU_LAI_7_2_1 (151%) => +1.38%
- BSI: MAU_LO_7_2_5 (-3.44%) (5.69%) (38.7%) => -8.21%
- GVR: MAU_LO_7_3_1 (4.1%) (21%) => -8.42%
- SHB: MAU_LO_7_3 (2.01%, 1.6%, 0.79%) (49.98%) => -7.63%
- VJC: MAU_LO_7_2_1 (-2.7%) => -0.38%
- DDV: MAU_LO_7_3_1 (4.31%, 0.93%, 1.41%) (137%) => -4.85%
- BFC: MAU_LO_7_2_5 (-3.82%) => -3.35%

#20260720
- FPT: MAU_LO_7_3_1(2.42%, 0.3%, 0.15%) (84%) => -3.87%

#20260722
- FTS: MAU_LO_7_7_1 (26.43%), (5.44%, 1.34%, 3.18%) => -5.09%
- BSI: MAU_LO_7_2 (-3.47%) => -2.84%
- BFC: MAU_LO_7_2 (-2.48%) => -6.45%

#20260723
- VPL: MAU_LO_7_2 (-4.63%) => -1.22%
- POW: MAU_LO_7_2 (-2.65%) => -1.22%
- DPM: MAU_LO_7_8 (-2.33%) (3.18%, 1.11%, 2.95%)=> -2.02%
- PVD: MAU_LO_7_2 (-5.%) => -1.09%

#20260727
- THD: MAU_LO_7_2 (-8.02%) => -0.57%

#20260728
- FPT: MAU_LAI_7_2_1 (21.35%) (3.58%, 1.78%, 1.29%) => +5.97%
- BSI: (-9.14%) (7.84%, 5.49%, 2.48%) => +3.93%
- BVS: (-8.23%) (18.64%, 15.18%, 6.7%) => +1.53%
- MBS: (-6.9%) (16.46%, 12.66%, 2.3%) => +3.26%
- TRC: MAU_LAI_7_1_3 (-22.7%) (0.67%, 0.67%, 0.67%) => +2.85%
- VIC: MAU_LAI_7_1_3 (-5.49%) (1.96%, 1.81%, 0.14%) => +2.82%
- CTG: MAU_LAI_7_1_3 (-23.22%) (2.82%, 2.11%, 0.87%) => +4.76%
- VCB: MAU_LAI_7_1_3 (+1%) (2.44%, 0.74%, 0.19%) => +4.25%
- TCB: MAU_LAI_7_1_3 (+1.42%) (2.88%, 1.24%, 0.88%) => +2.73%
- TPB: MAU_LAI_7_4 => +2.43%
- BID: => 5.77%
- VPB: MAU_LAI_7_1_3 (-5.14%) (3.13%, 2.07%, 0.2%) => +1.6%
- POW: MAU_LAI_7_2_1 (80.54%) (3.1%, 1.53%, 0.76%) => +2.92%
- HDG:
- PVD: MAU_LAI_7_1_3 (-20.99%) (1.94%, 0.27%, 0.27%) => +2.91%
- PVT: MAU_LAI_7_1_4 (-50.35%) (4.05%, 2.78%, 2.15%) => +8.26%
- OIL: MAU_LAI_7_1_3 (-32.38%) (3.18%, 0.78%, 0.78%) => +2.99%
- TVN: nến T nằm sát giá mở cửa của T-1

=============
- NLG: MAU_LAI_x_3 