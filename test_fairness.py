import pandas as pd
import numpy as np
import pingouin as pg

np.random.seed(42)
n = 100
data = {
    'ward_income_proxy': np.random.normal(50000, 15000, n),
    'pollution_contribution': np.random.normal(50, 20, n),
    'population_exposure': np.random.normal(10000, 3000, n),
}
data['priority_score'] = (data['pollution_contribution'] * 0.6 + 
                          (data['population_exposure'] / 1000) * 0.4 + 
                          np.random.normal(0, 5, n))

df = pd.DataFrame(data)
pcorr = pg.partial_corr(data=df, x='priority_score', y='ward_income_proxy', covar=['pollution_contribution', 'population_exposure'])
print(pcorr)
print(f"\nPartial correlation (r) = {pcorr['r'].values[0]:.3f}")
if abs(pcorr['r'].values[0]) < 0.1:
    print("✅ Fairness Audit Passed: Priority score is independent of ward income.")
else:
    print("❌ Failed")
