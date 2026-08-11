# 1. Mãu lỗ lãi
=========================================================
- MAU_LAI_7_1  	: 7 điểm, vol T < T-1 (arg1)
- MAU_LAI_7_1_1	: MAU_LAI_7_1, biên độ T cao (arg2), Nến cắm hương giá đóng cửa gần sát với giá mở cửa và giá thấp nhất 
- MAU_LAI_7_1_2	: MAU_LAI_7_1, biên độ T cao (arg2), nến cover cả phiên T-1, vol T-1 so với ma20: -3.8%: need check

- MAU_LAI_7_2	: 7 điểm, giá đóng cửa T nằm giữa mở cửa và đóng cửa T-1 còn giá mở cửa T < T-1 đóng cửa, vol T lớn hơn nhiều T-1(arg1)
=========================================================
- MAU_LO_7_1   	: 7 điểm, nến cắm hương giá đóng cửa sát gần với giá mở cửa, vol T >= 1.5 * vol T-1 (arg1)

- MAU_LO_7_2   	: 7 điểm, T-1 phiên giảm điểm lớn < -2.5% (arg1), Biến động giá T nhỏ (arg2) và giá đóng cửa gần mức thấp nhất, vol tương đương (ar3)
- MAU_LO_7_2_1 	: 7 điểm, T-1 phiên giảm điểm lớn < -2.5% (arg1), Biến động giá T lớn (arg2), vol T = 1.07 T-1 gần tương đương
- MAU_LO_7_2_2 	: 7 điểm, T-1 phiên giảm điểm lớn < -2.5% (arg1), Biến động giá T nhỏ (arg2) và giá gần với mức cao nhất, vol tương đương(ar3)
- MAU_LO_7_2_3 	: 7 điểm, T-1 phiên giảm điểm lớn < -2.5% (arg1), Biến động giá T lớn (arg2) và giá gần với mức cao nhất, vol T nhỏ hơn rất nhiều T-1(ar3)
- MAU_LO_7_2_4 	: 7 điểm, T-1 phiên giảm điểm lớn < -2.5% (arg1), Biến động giá T nhỏ (arg2) và giá gần với mức cao nhất, vol T nhỏ hơn rất nhiều T-1(ar3)
- MAU_LO_7_2_5 	: 7 điểm, T-1 phiên giảm điểm lớn < -2.5% (arg1), Biến động giá T lớn (arg2) và giá gần với mức cao nhất, vol T lớn hơn T-1(ar3)


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
- MAU_HOLDING_1: 

# 20260701
- NVL: MAU_LO_7_1,  volume T = 2.06*T-1 => -2.03%
- DGC: MAU_LO_7_2, (-2.51%), (+0.21%) => -0.42%
- GAS: MAU_LO_7_1, Vol = 1.44 * T-1 => -3.59%
- HSG:MAU_LO_7_3, biên độ giá rất nhỏ 0.43%,vol T  = 1.42 * T-1

#20260703
- PVC: MAU_LO_7_2, nến  T-1 đỏ đặc bao chùm lên nến xanh T-2, (-2.31%),  => Hồi ở phiên T và có thể giảm ở phiên tiếp theo, vol T > 1.1 T-1 => -0.47%
- NKG: tương tự PVC nhưng vol T >1.7 T-1 => 0%

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

#20260713
- GEE: MAU_LO_7_6 (0.12%, 0.37%) => -0.5%
- CII: MAU_LO_7_1 (1.49%) => -2.53%
- VPL: MAU_LO_7_5 => 1.34%
- PVS: MAU_LO_65_2 => +2.63%

#20260714
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
- FOC: MAU_LAI_7_2 (151%) => +1.38%
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

