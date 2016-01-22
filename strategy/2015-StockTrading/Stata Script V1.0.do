* This program is intended to implement the automated stock trading strategy

* Program version 1.0
* Last update Jan/23/2015

clear all 													// Leave matrix uncleared
clear mata
macro drop _all
program drop _all
set varabbrev off


****************** Program Settings ******************
global Folder 			= "D:\Dropbox\Projects\2015 - Stock Trading"		// Location of program scripts
global Output_Folder	= "D:\Workspace\Outputs" 
global Temp_Folder 		= "D:\Workspace\Temp"									// Location to which temporary files are generated
global CRSP_Folder  	= "D:\Workspace\CRSP"								// Location of the original data files (ASCII)
global CompuStats_Folder= "D:\Workspace\CompuStats"
global Factors_Folder 	= "D:\Dropbox\Resources\Datasets\Market Factors"	// Location of the market factors
global LoadData 		= "No" 												// "Yes" to load the CRSP datasets into a panel dataset
global ShowStats 		= "No" 												// Choose "Yes" or "No"; "Yes" would show all summary statistics during the process (incl. diagrams).
global MonthlyData 		= "No" 												// Convert data from daily to monthly
global Start_Year 		= 2000 
global Start_Month 		= 1
global Start_Date 		= 1
global Train_Set_Period = 12
global Test_Set_Period  = 1
global MinObsPercentage = 0.7 												// Set the percentage of minimum obsrevations for in-sample and for post-sample period. 
																			// For example, 70% implies that if the sample window is 3 years, each fund must at least report 3*12*0.7=25.2 monthly returns during the insample period, and 8.4 months during the post-sample period.
global Weighted_Return 	="No"												// OLS dependent var as excess return weighted by assets																		
global Category_By_Clusters = "Yes" 										// Categorise stocks using K-Means rather than industry code
global Min_R2 			= 0.6						// Reject OLS regression if R2 fall below this threshold
global Max_Fstat		= 0.1						// Reject OLS regression if f-test's p-value is above this threshold	
global Min_Obs 			= 0.02 								// Mininum number of observations in each category; if fall below this threshold, small categories will be merged.
* Variable speicification
global CRSP_Vars 		= "permno date prc ret sprtrn shrout siccd cusip comnam ticker primexch" 							// Variables to be extracted from the CRSP datasets
global Varlist  		= "fac1 fac2 fac3 fac4 fac5 fac6 fac7 fac8"
******************************************************

* PROGRAM STARTS HERE *
{
* Other environmental variables
cap set procs_use 4
cap set memory 12g
#delimit cr
set trace off
set more off
cap set maxvar 20000
cap set matsize 11000
set scrollbufsize 2048000
set dp period
set scheme s1color
set printcolor automatic
set copycolor automatic
set autotabgraphs on
set level 95
set maxiter 16000
set varabbrev off
set reventries 32000
*set maxdb 500
set seed 999						
set type double
set logtype text
pause on
*sysdir set PERSONAL "$Temp_Folder\ado"
*sysdir set PLUS "$Temp_Folder\ado\plus"
*sysdir set OLDPLACE "$Temp_Folder\ado" 
*net set ado PERSONAL
set rmsg on
cd "$Folder"
}

* Functions *
cap program drop K_Means
program K_Means
{
	global Min_Obs = 100 		// if less than Min_Obs fall into one category, this category is removed.

	use "$CompuStats_Folder\\Annual.dta", clear

	keep datadate tic cusip sale che act capx bkvlps ceq csho uniami xint xrd ppegt adrr bkvlps csho cdvc lt sic 
	
	gen yr = year(datadate)
	gen qt = quarter(datadate)
	gen t = yofd(datadate)
	
	rename tic ticker
	
	// strip cusip
	replace cusip = substr(cusip, 1, 8)
	
	// drop duplicates
	sort cusip t
	by cusip t: gen dup = _n
	tab dup
	drop if dup>1
	drop dup
		
	// Calculate two-year geometric average of annual growth rate in net sales 
	sort cusip t
	by cusip: gen lSale = sale[_n-1]
	by cusip: gen l2Sale = sale[_n-2]
	gen lSGro = (lSale - l2Sale)/l2Sale
	gen sGro = (sale - lSale)/lSale
	gen sGrowth = sqrt(lSGro*sGro)
	drop lSale l2Sale lSGro sGro
		
	// Cash and short-term investments divided by total assets
	gen cash = che/act
	
	// Capital expenditures divided by total assets
	gen capex = capx/act
	
	// Market value of equity divided by book value of equity
	gen bookToMarket = bkvlps/(ceq/csho)
	gen mb = 1/bookToMarket
		
	// ROA
	gen roa = (uniami + xint)/act
	
	// R&D Research and development expenditures divided by total assets
	gen rnd = xrd/act
	
	// PPE: Property plant and equipment divided by total assets
	gen ppe = ppegt/act
	
	// ADR
	gen adr = 0
	replace adr = 1 if adrr>0 & adrr<.
		
	// Tobin's Q: total asset plus market value of equity minus book value of equity
	// divided by total asset
	gen tobinQ = (act + ceq - bkvlps*csho)/act
	
	// Dummy that equals one if cash divideds are positive, zero otherwise
	gen divCash = 0
	replace divCash = 1 if cdvc>0 & cdvc<.
		
	// Turnover: share volume divided by adjusted shares outstanding
	*N/A
	
	// Get 4 Variables
	
	// Total assets: act
	// Book Value Per Share: bkvlps
	// Common/Orindary Equity - Total: ceq
	// Common Shares Outstanding: csho
	// Current Liabilities - Total: lct
	// Liabilities - Total: lt
	
	gen totalAsset = act
	gen leverageRatio =  lt/ceq


	tostring sic, replace
	gen siccdMajor = substr(sic, 1, 2)
	tab siccdMajor
	drop if siccdMajor=="."
	drop if siccdMajor=="9"
	encode siccdMajor, generate(cat)	
	drop siccdMajor
	
	tab cat, gen(bin_cat)
	
	forvalues year = 1990/2013 {
		preserve
		
		keep if yr==`year'
		
		global vars = "sGrowth cash capex bookToMarket mb ppe tobinQ divCash totalAsset leverageRatio"
		foreach x of global vars {
			rename `x' `x'_
			egen `x' = std(`x'_)
			drop `x'_
			replace `x' = 0 if `x'==.
		}
		
		cap cluster delete category
		cluster k $vars bin_cat*, k(20) name(category) s(kr(88888)) keepcen 
		cluster delete category
		tab category
		local rows = r(r)
		
		forvalues i = 1/`rows' {
			count if category==`i'
			replace category = . if category==`i' & r(N)<$Min_Obs
		}
		replace category = -1 if category==.
		tab category
		
		tostring category, gen(cat_)
		drop category
		encode cat_, generate(category)	
		drop cat_
		
		tab category
		
		rename yr merge_yr
		keep merge_yr cusip category
		
		duplicates drop
		
		save "$Temp_Folder\\`year'_category.dta", replace
		restore
	}
}
end program	


cap program drop change_date
program change_date
	* change the date of the market factors
{	
	gen date2 = date(date, "YMD")
	format date2 %td
	drop date
	rename date2 date
	order date
	sort date
}
end program

cap program drop prepare_factors
program prepare_factors
{
	* prepare the market factors from raw data
	
	* Import Fama French Factors
	import delimited "D:\Dropbox\Resources\Datasets\Market Factors\F-F_Research_Data_Factors_daily.txt", delimiter(space, collapse) clear
	tostring date, replace
	change_date

	save "D:\Workspace\Fac1.dta", replace

	* Import MSCI EEM 
	import delimited "D:\Dropbox\Resources\Datasets\Market Factors\MSCI EEM.csv", delimiter(comma) clear 
	change_date
	keep date adjclose
	rename adjclose msci_eem
	save "D:\Workspace\Fac2.dta", replace

	* import PTFSX
	import delimited "D:\Dropbox\Resources\Datasets\Market Factors\PTFSX.csv", delimiter(comma) clear 
	change_date
	keep date adjclose
	rename adjclose ptfsx
	save "D:\Workspace\Fac3.dta", replace

	* import Russell 2000
	import delimited "D:\Dropbox\Resources\Datasets\Market Factors\Russell2000.csv", delimiter(comma) clear 
	change_date
	keep date adjclose
	rename adjclose russ2000
	save "D:\Workspace\Fac4.dta", replace

	* import s&p 500
	import delimited "D:\Dropbox\Resources\Datasets\Market Factors\S&P500.csv", delimiter(comma) clear 
	change_date
	keep date adjclose
	rename adjclose sp500
	save "D:\Workspace\Fac5.dta", replace

	* import T-bond 5yr yield
	import delimited "D:\Dropbox\Resources\Datasets\Market Factors\TreasuryYield.csv", delimiter(comma) clear 
	change_date
	keep date adjclose
	rename adjclose tbond
	save "D:\Workspace\Fac6.dta", replace

	use "D:\Workspace\Fac1.dta", clear
	merge 1:1 date using "D:\Workspace\Fac2.dta", nogen
	merge 1:1 date using "D:\Workspace\Fac3.dta", nogen
	merge 1:1 date using "D:\Workspace\Fac4.dta", nogen
	merge 1:1 date using "D:\Workspace\Fac5.dta", nogen
	merge 1:1 date using "D:\Workspace\Fac6.dta", nogen

	forvalues i = 1/6 {
		erase "D:\Workspace\Fac`i'.dta"
	}

	sort date
	gen time = _n
	tsset time

	* factor 1, 2, 3: Fama French 3 factors
	gen fac1 = mktrf
	gen fac2 = smb
	gen fac3 = hml

	* factor 4: Size factor is the difference between Russell 2000 return - S&PCOMP return
	gen russ2000_ret = D.russ2000/L.russ2000
	gen sp500_ret = D.sp500/L.sp500
	gen fac4 = russ2000_ret - sp500_ret

	* factor 5: The emerging market factor is the return computed from the MSCI EM U$
	gen fac5 = D.msci_eem/L.msci_eem

	* factor 6:  Equity market factor is the return computed from S&P 500 Composite
	gen fac6 = D.sp500/L.sp500

	* factor 7: 4. Credit spread factor is calculated using monthly change in Baa yield - 10-year Treasury yield

	* factor 8: Bondmarket factor is the monthly change in 10-year Treasury
	gen fac7 = D.tbond/L.tbond

	* factor 8: PTFSFX: Return of PTFS Currency Lookback Straddle
	gen fac8 = D.ptfsx/L.ptfsx

	* Fill in 0 for missing
	forvalues i = 1/8 {
		replace fac`i' = 0 if fac`i'==.
	}

	keep date rf sp500 fac*
	save "$Factors_Folder\\factors.dta", replace
}
end program

cap program drop compareList
program compareList
args listLength sorting
	* Compare the number of correct predictions in top/bottom lists in the test-set
	
	foreach x of global VarName {
		qui{
				preserve
					replace `x'_s = `x'_s*`sorting'
					sort `x'_s 		// rank Alphas from the in-sample period	
					keep if _n<=`listLength'
					mkmat firmID, matrix(mat_`x'_s)
				restore
				preserve
					replace `x'_p = `x'_p*`sorting'
					sort `x'_p 		// rank Alphas from the post-sample period	
					keep if _n<=`listLength'
					mkmat firmID, matrix(mat_`x'_p)
				restore	
				
				local countCorrect = 0
				local alphaInSample = 0
				local alphaPostSample = 0
				
				forvalues i = 1/`listLength' {
					* reading in alpha from the first row of in-sample to the last row
					local alphaInSample = mat_`x'_s[`i',1]
					forvalues j = 1/`listLength' {
						* read in alpha from the 1st row to the end of post-sample
						if `alphaInSample'==mat_`x'_p[`j',1] {
							local countCorrect = `countCorrect' + 1 
						}
						*disp "number of correct is :" `countCorrect'
					}
				}
			}
		if `sorting'==1 local listName = "Bottom"
		if `sorting'==-1 local listName = "Top"	
		disp "`countCorrect' out of `listName' `listLength' are correct, using specification `x'"
		
		local temp = r(rho)
		file write tableRoll "Spec `x', `countCorrect'" _n		
	}
end program


cap program drop ChangeVarNames
program ChangeVarNames
	* Temp funtions need to be depleted
	local varlist = "eb_ew eb_ew_o1 eb_ew_o2 eb_vw eb_vw_o1 eb_vw_o2"
	foreach x of local varlist {
		cap rename `x' `x'_temp
	}
	foreach x of local varlist {
		cap replace `x' = `x'_temp if `x'==.
	}	
end program	

cap program drop firmCount
program firmCount
	* Stats on the number of observations
{	
	disp "* Statistics of Companies in the Current Dataset:"
	qui count
	disp "    - Total Observations: " r(N)
	cap drop dup
	qui {
			* calculate the number of firms
			sort permno
			by permno: gen dup = _n
			replace dup = 0 if dup>1
			egen numberOfFunds = total(dup)
			sum numberOfFunds
			global firmNumber = r(mean)
		}
	qui count	
	disp "    - Total Number of Firms: " $firmNumber

	preserve 
		qui drop if dup~=1
		qui keep permno category
		disp ""
		disp "* Tabulation of Funds by Category: "
		tab category
	restore
	
	qui drop dup numberOfFunds
	sort permno month date
}
end program	


* Main Program
cap program drop main
program main
	disp "*******************************************************"		
	disp " S1. Prepare Dataset 1990 - 2013"
	disp "*******************************************************"	
		if "$LoadData"=="Yes" {
			if "$Category_By_Clusters"=="Yes" {
				*S0.9 To carry out cluster analysis to define categories
				K_Means
			}
			*S1.0 Prepare market factors
			prepare_factors
			
			*S1.1 Load data from CRSP
		
			* shrink CRSP data
			forvalues yr = 1980/2013 {
				use "$CRSP_Folder\\`yr'.dta", clear
				keep $CRSP_Vars
				save "$Temp_Folder\\CRSP_`yr'.dta", replace
			}
	
			clear
			forvalues yr = 1990/2013 {
				append using "$Temp_Folder\\CRSP_`yr'.dta"
			}
		
			// Drop missing prc
			drop if prc==.
			replace prc = - prc if prc<0 		// some prc are negative due to imputation by CRSP
			
			* remove duplicates
			sort permno date prc ret
			by permno date: gen dup = _n
			by permno date: egen maxDup = max(dup)		
			tab maxDup
			drop if dup>1
			drop dup maxDup

			if "$MonthlyData"=="Yes" {
				gen month = mofd(date)
				sort permno month date		
			
				* Calculate cumulative return for each month
				gen lnRet = ln(1+ret)
				by permno month: egen monthlyRetE = total(lnRet)
				gen monthlyRet = exp(monthlyRetE)-1
				drop lnRet monthlyRetE
				drop ret 
				rename monthlyRet ret

				* Collapse to monthly data
				by permno month: gen dup = _n
				by permno month: egen maxDup = max(dup)
				keep if maxDup==dup
				drop dup maxDup			
			}
		
			sort permno date
			
		*S1.3 Merge with factor variables
			// Prepare 9 factors
			/*
			use "D:\Dropbox\Resources\Datasets\Lippers Tass\Factor.dta", clear
			// Declare time series
			gen double month = monthly(time, "YM")
			replace month = month - `small' + 1
			drop time
			save "$Temp_Folder\\Factors.dta", replace
			*/
			
			merge m:1 date using "$Factors_Folder\\factors.dta"
			drop if _merge==2
			drop _merge
							
			*S1.4 Generate some variables
			// define excess return at t
			gen exRet = ret - rf 		
		
			// Generate time variables
			gen yr 		= year(date)
			gen mon 	= month(date)
			gen month 	= mofd(date)
			
			compress
			
			save "$Temp_Folder\\CRSP_All.dta", replace
		}
		
	disp "*******************************************************"		
	disp " S2. Define Training Set and Test Set"
	disp "*******************************************************"			
		use "$Temp_Folder\\CRSP_All.dta", clear
		
		// Train Set begin the the 1st of the month
		scalar TrainSetStart = mdy($Start_Month, $Start_Date, $Start_Year)
		// Train set ends at the end of the month
		scalar TrainSetEnd = dofm(mofd(TrainSetStart) + $Train_Set_Period) - 1
		// Test set ends at the end of the month. 
		scalar TestSetEnd = dofm(mofd(TrainSetEnd) + 1 + $Test_Set_Period) - 1
		
		// Identify in-sample observations
		gen inSample = (date>=TrainSetStart & date<=TrainSetEnd)
		// post-sample observations
		gen postSample = (date>TrainSetEnd & date<=TestSetEnd)
		
		keep if inSample==1 | postSample==1
		
		if "$Category_By_Clusters"=="Yes" {
			tostring siccd, replace
			gen siccdMajor = substr(siccd, 1, 1)
			tab siccdMajor
			drop if siccdMajor=="."
			drop if siccdMajor=="9"
			drop siccdMajor
			
			sum yr
			local _mergeYr = r(min)
			gen merge_yr = `_mergeYr'
			merge m:1 cusip merge_yr using "$Temp_Folder\\`_mergeYr'_category.dta"
			drop if _merge==2
			drop merge_yr
			drop _merge
			
			tab category
			local rows = r(r)
			disp "`rows'"
			forvalues i = 1/`rows' {
				local frac = r(N)/_N
				replace category = . if category==`i' & `frac'<$Min_Obs
			}
			drop if category==.
			tab category, gen(d_cat)
			
			drop category
			gen category = 1
			forvalues i = 1/`rows' {
				replace category = `i' if d_cat`i'==1
			}
			drop d_cat*
			
		}
		else {
			tostring siccd, replace
			gen siccdMajor = substr(siccd, 1, 1)
			tab siccdMajor
			drop if siccdMajor=="."
			drop if siccdMajor=="9"
			encode siccdMajor, generate(category)	
			drop siccdMajor
			
			tab category
			local rows = r(r)
			disp "`rows'"
			forvalues i = 1/`rows' {
				count if category==`i'
				local frac = r(N)/_N
				replace category = . if category==`i' & `frac'<$Min_Obs
			}
			drop if category==.
			tab category, gen(d_cat)
			local rows = r(r)

			drop category
			gen category = 1
			forvalues i = 1/`rows' {
				replace category = `i' if d_cat`i'==1
			}
			drop d_cat*		
			tab category
		}
		sort permno date
		
		disp "Dataset successfully loaded"
		
	disp "*******************************************************"		
	disp " S3. Impute Estimated Market Cap "
	disp "*******************************************************"			

	*S2.1 Generate some variables to access the proportion of data in which the estiamted assets are missing
		gen marketCap = shrout*1000 * prc
		
		disp "If Market Cap is zero, they are replaced to missing"
		replace marketCap=. if marketCap==0
		
		gen missingAsset = 0
		replace missingAsset = 1 if marketCap==.
		
		sum missingAsset
		/*
		if r(mean)~=0 {
			by permno: gen countByDate = _n
			by permno: egen fundObs = max(countByDate)
			drop countByDate
		
			by permno: egen totalMissingAsset = total(missingAsset)
			gen noMissingAsset = totalMissingAsset==0
			gen someMissingAsset = totalMissingAsset>0 & totalMissingAsset<fundObs
			gen allMissingAsset = totalMissingAsset==fundObs
			
			tabstat noMissingAsset someMissingAsset allMissingAsset, stat(n mean sd min max) col(stat) varwidth(16)
			drop totalMissingAsset noMissingAsset someMissingAsset allMissingAsset
			
		}	
		*/
		drop missingAsset
		
	
	*S2.2 Calcualte weighted average returns on assets
	if "$Weighted_Return"=="Yes" {
		sort date permno
		by date: egen totalMarketCap = total(marketCap)

		gen asset_weights = marketCap/totalMarketCap
		gen weighted_ret = asset_weights*(ret - rf)
		drop asset_weights
		drop totalMarketCap
		drop ret
		rename weighted_ret ret
		sort permno month date
	}					
	disp "*******************************************************"		
	disp " S3. Getting some statistics"
	disp "*******************************************************"		
	disp " "
		if "$ShowStats"=="Yes" {

			preserve
				disp " "
				firmCount
				
				disp " "	
				disp "* Number of firms in the CRSP database on the cut-off date: " year(cutOffDay) ", Month " month(cutOffDay)
				qui {
					by permno: egen lastdate = max(month)
					gen reportedLastDay_temp = lastdate==month
					by permno: egen reportedLastDay = max(reportedLastDay_temp)				
					
					drop if countByMonth>1
					count if reportedLastDay==1
				}			
				disp "# companies reported on Cut-Off date: " r(N) ", out of total " $fundNumber " firms."
			restore 

			disp " "	
			disp "* Tabulation of the listing period"
			preserve
				qui {
					sort permno
					by permno: egen firmDuration = max(countByMonth )
					drop if countByMonth>1
				}
				disp "e.g. Tabulation of number of monthly returns reported by each fund"
				qui sum firmDuration
				qui gen full = firmDuration==r(max)
				qui sum full
				disp r(mean)*100 "% of observations are listed during the entre samplying period."
				*hist firmDuration, freq
			restore
			
				*ShowStat
	
			sort permno month date
			by permno: gen countByMonth = _n
			by permno: egen firmObs = max(countByMonth)
			
			// Count the number of observations for each firm
			by permno: egen sumRet = total(ret)
			by permno: gen meanRet = sumRet/firmObs
			drop firmObs countByMonth 
		
			preserve
				disp "* Statistics of Mean Returns:"
				qui keep permno meanRet
				qui duplicates drop
				tabstat meanRet, stat(n mean sd min max) col(stat) varwidth(16)
				*drop if meanRet>60
				*tab firmObs
				*hist meanRet, freq title(Distribution of Mean Returns (Sample with mean returns less than 60)) 
				* plot the distribution of the mean returns for each firm
				*pause
			restore	
				
			// find the number of missing returns for each firm
			sort permno month date
			by permno: gen countByMonth = _n
			by permno: egen firmObs = max(countByMonth)
			
			gen lastdateTmp = 0
			replace lastdateTmp = mofd(date) if countByMonth==firmObs
			by permno: egen lastMonth = max(lastdateTmp)
			gen firstdateTmp = 0
			replace firstdateTmp = mofd(date) if countByMonth==1
			by permno: egen firstMonth = max(firstdateTmp)
			drop lastdateTmp firstdateTmp

			gen numberOfMonths = lastMonth - firstMonth + 1
			gen missingMonths = numberOfMonths - firmObs
			sum missingMonths	
			
			drop firmObs countByMonth 				
		
			preserve
				disp "* Statistics of missing months of each firm:"
				disp "   Note: Only firms with some missing months are considered,"
				disp "         firms with full reported history are excluded."
				qui keep permno missingMonths
				qui duplicates drop
				qui drop if missingMonths==0
				qui count
				disp "    - # firms with missing monthly return: " r(N)
				disp ""
				disp "Statistics of Missing Month:"
				sum missingMonths
				disp ""
				disp "Tabulation of Missing Month:"
				tab missingMonths
				*hist missingMonths, freq width(5) title(Number of Months Missing) 
				*pause
			restore


		}
		

disp "*******************************************************"		
disp " S4. Further Filter Data"
disp "*******************************************************"	
	disp "* S4.1. Dropping observations s.t. criteria"
		disp "* Drop firms with too few observations in In-Sample Period"
		qui {
			sort permno month date
			by permno: gen periods_temp = _n
			replace periods_temp = 0 if inSample==0
			by permno: egen periods = max(periods_temp)			
		}
		
		if "$ShowStats"=="Yes" {
			firmCount
			local temp1 = $firmNumber 
		}
		
		qui sum periods
		drop if periods < r(max)*$MinObsPercentage
		drop periods 
		drop periods_temp
		
		if "$ShowStats"=="Yes" {
			firmCount
			local temp2 = `temp1' - $firmNumber
			disp "# firms excluded due to too few obs in sample, `temp2'" _n	
		}
		
		disp "* Drop firms with too few observations in Post-Sample Period"
		qui {
			gen date_inv = - date
			sort permno date_inv
			by permno: gen periods_temp = _n
			replace periods_temp = 0 if postSample==0
			
			by permno: egen periods = max(periods_temp)
			
		}
		
		if "$ShowStats"=="Yes" {
			firmCount
			local temp1 = $firmNumber 	
		}
		qui sum periods
		drop if periods<r(max)*$MinObsPercentage
		drop periods periods_temp
		
		if "$ShowStats"=="Yes" {		
			firmCount
			local temp2 = `temp1' - $firmNumber
			disp "# firms excluded due to too few obs in postsample, `temp2'" _n		
		}
		
		disp "* Drop firms if category is Undefined"
		drop if category==.

		disp "* Drop obs if any missing values in the factors"
		foreach x of global Varlist {
			drop if `x'==.
		}
			
		sort permno month date 

		disp "* Some category may have market cap equal to zero. "
		disp "* These categories are excluded"
		tab category
		local cat_num = r(r) 
		forvalues i = 1/`cat_num' {
			qui sum marketCap if category==`i'
			if r(max)==0 {
				disp "******************** WARNING *********************"
				disp "Category `i' is found to have missing estimated assets"
				disp "Category `i' is excluded"
				disp "******************** WARNING *********************"
				drop if category==`i'
			}
		}
	
disp "*******************************************************"		
disp " S5. Construct Peer Review Factor "
disp "*******************************************************"		
	disp "* S5.1. Calculate EW and VW index"
	*S4.2a Equal-weighted Index (Un-Orthogonalised); Eq. (1)
		preserve
			// Count number of firms per Primary Category
			sort category date
			
			by category date: gen count_temp = _n
			by category date: egen count_cat = max(count_temp)
			
			// gen sum of excess returns - numerator
			sort category date
			by category date: egen numer = sum(exRet)

			gen eb_ew = numer/count_cat

			keep eb_ew category date inSample postSample
			duplicates drop
			save "$Temp_Folder\\Panel_EW.dta", replace
				
			merge m:1 date using "$Factors_Folder\\factors.dta"
			drop if _merge==2
			drop _merge
			
			gen eb_ew_o1 = .
			gen eb_ew_o2 = .
			
			save "$Temp_Folder\\temp.dta", replace
			
			// EWO In Sample
			use "$Temp_Folder\\temp.dta", clear
			keep if inSample==1
			
			tab category
			local cat_num = r(r) 
			
			forvalues i = 1/`cat_num' {
				qui count if category==`i'
				disp "# Observations in Category `i': " r(N)
				regress eb_ew $Varlist if category==`i'
				predict eb_hat
				
				gen resid = eb_ew - eb_hat	
				** a: Orthogonalised peer group benchmark; Eq. (5)
				replace eb_ew_o1 = _b[_cons] + resid if category==`i'
				** b: Orthogonalised peer group benchmark; Eq. (6)
				replace eb_ew_o2 = resid if category==`i'
				drop resid eb_hat
			}
			keep date category eb_ew eb_ew_o1 eb_ew_o2 inSample
			save "$Temp_Folder\\inSample_EWO.dta", replace
			
			// EWO Post Sample
			use "$Temp_Folder\\temp.dta", clear
			keep if postSample==1
			forvalues i = 1/`cat_num' {
				regress eb_ew $Varlist if category==`i'
				predict eb_hat
				gen resid = eb_ew - eb_hat	
				** a: Orthogonalised peer group benchmark; Eq. (5)
				replace eb_ew_o1 = _b[_cons] + resid if category==`i'
				** b: Orthogonalised peer group benchmark; Eq. (6)
				replace eb_ew_o2 = resid if category==`i'
				drop resid eb_hat
			}
			keep date category eb_ew eb_ew_o1 eb_ew_o2 postSample
			save "$Temp_Folder\\postSample_EWO.dta", replace
		restore

	*S4.2b Value-weighted Index; Eq. (2)
		preserve
			sort category date
			by category date: egen numer = total(exRet*marketCap)
					
			// Count number of firms per Primary Category
			by category date: egen denom = total(marketCap)
			
			gen eb_vw = numer/denom

			keep eb_vw category date inSample postSample
			duplicates drop
			save "$Temp_Folder\\Panel_VW.dta", replace
			
			merge m:1 date using "$Factors_Folder\\factors.dta"
			drop if _merge==2
			drop _merge

			gen eb_vw_o1 = .
			gen eb_vw_o2 = .		
			
			save "$Temp_Folder\\temp.dta", replace
			
			// VWO In Sample
			use "$Temp_Folder\\temp.dta", clear		
			keep if inSample==1
			
			tab category
			local cat_num = r(r) 
			
			forvalues i = 1/`cat_num' {
				qui count if category==`i'
				disp "# Observations in Category `i':" r(N)			
				regress eb_vw $Varlist if category==`i'
				predict eb_hat
				gen resid = eb_vw - eb_hat	
				** a: Orthogonalised peer group benchmark; Eq. (5)
				replace eb_vw_o1 = _b[_cons] + resid if category==`i'
				** b: Orthogonalised peer group benchmark; Eq. (6)
				replace eb_vw_o2 = resid if category==`i'
				drop resid eb_hat
			}
			
			keep date category eb_vw eb_vw_o1 eb_vw_o2 inSample
			save "$Temp_Folder\\inSample_VWO.dta", replace		
			
			// VWO Post Sample
			use "$Temp_Folder\\temp.dta", clear				
			keep if postSample==1
			forvalues i = 1/`cat_num' {
				regress eb_vw $Varlist if category==`i'
				predict eb_hat
				gen resid = eb_vw - eb_hat	
				** a: Orthogonalised peer group benchmark; Eq. (5)
				replace eb_vw_o1 = _b[_cons] + resid if category==`i'
				** b: Orthogonalised peer group benchmark; Eq. (6)
				replace eb_vw_o2 = resid if category==`i'
				drop resid eb_hat
			}
			keep date category eb_vw eb_vw_o1 eb_vw_o2 postSample
			save "$Temp_Folder\\postSample_VWO.dta", replace		
		restore		
		
	
disp "*******************************************************"	
disp " S4. OLS Regressions "
disp "*******************************************************"	

	* Model specifications
	* a. Non-inclusion of any peer group benchmark (?o EB?, corresponding to equa-tion (4).
	* b. Inclusion of a non-orthogonalized peer group benchmark (?B non-ortho.?
	* c. Inclusion of an orthogonalized peer group benchmark ?Use of epsilons e plus benchmark-alphas a (?B = a+e?, i.e., corresponding to equation (12).
	* d. Inclusion of an orthogonalized peer group benchmark without the benchmark-alphas ?Use of the epsilons e only (?B = e?, i.e., corresponding to equation (13).
	
	*S5.1 Prepare Data
		merge m:1 date category inSample using "$Temp_Folder\\inSample_EWO.dta"
		drop _merge
		ChangeVarNames
		merge m:1 date category inSample using "$Temp_Folder\\inSample_VWO.dta"
		drop _merge
		ChangeVarNames
		merge m:1 date category postSample using "$Temp_Folder\\postSample_EWO.dta"
		drop _merge
		ChangeVarNames
		merge m:1 date category postSample using "$Temp_Folder\\postSample_VWO.dta"
		drop _merge
		ChangeVarNames
		drop *_temp
		
		// There are some missing numbers in the indices
		********************* WARNING! ***********************
		disp "WARNING: No observations should be dropped below."
		disp "    if any observations are excluded, check the reasons of missing values in the indices "
		******************************************************
		sum eb_ew eb_ew_o1 eb_ew_o2 eb_vw eb_vw_o1 eb_vw_o2
		local varlist = "eb_ew eb_ew_o1 eb_ew_o2 eb_vw eb_vw_o1 eb_vw_o2"
		foreach x of local varlist {
			drop if `x'==.
		}	

		/*
		// Drop unnecessary obs as the result of the merge process		
		sort permno month date
		by permno: gen periods_temp = _n
		replace periods_temp = 0 if inSample==0
		
		sort permno
		bysort permno: egen periods = max(periods_temp)		
		drop if periods<$minTimeSpan
		drop periods_temp periods	
 
		gen month_i = - month
		sort permno month_i
		bysort permno: gen periods_temp = _n
		replace periods_temp = 0 if postSample==0
		bysort permno: egen periods = max(periods_temp)
		sum periods
		drop if periods<$minTime_Post
		drop periods_temp periods month_i
		sort permno month date
		
		// Check again sample size for each firm
		gen fail = 0
		replace fail = 1 if inSample==1 & ( exRet==. | fac1==. | fac2==. | fac3==. | fac4==. | fac5==. | fac6==. | fac7==. | fac8==. )
		replace fail = 1 if postSample==1 & ( exRet==. | fac1==. | fac2==. | fac3==. | fac4==. | fac5==. | fac6==. | fac7==. | fac8==. )

		sort permno month date
		by permno: egen _fail = max(fail)
		drop if _fail==1
		drop fail _fail
		*/

		// generate firmID
		sort permno month date
		by permno: gen seq = _n
		replace seq = 0 if seq>1
		gen firmid = seq[1]
		replace firmid = seq[_n] + firmid[_n-1] if _n>1
		drop seq

		tab category
		global Cat_num = r(r)
		sum firmid
		global firm_num = r(max)

		save "$Temp_Folder\\finalData.dta", replace
		keep if inSample==1
		disp "Running OLS regressions"
		statsby _b e(r2) e(F) e(df_m) e(df_r) _se, by(firmid) verbose clear: regress exRet $Varlist eb_vw_o1 

		local test_begin = TrainSetEnd + 1
		local test_end	 = TestSetEnd
		local yr = year(TestSetEnd)
		local mon = month(TestSetEnd)
	
		save "$Output_Folder\\OLS-`yr'-`mon'.dta", replace

		
disp "*******************************************************"	
disp " S5. Calculate Portfolio Performance "
disp "*******************************************************"	
	use "$Output_Folder\\OLS-`yr'-`mon'.dta", clear
	
	* Exclude if r2 is too low
	drop if _eq2_stat_1<$Min_R2
	* Exclude if F-stats is too low
	gen f_test = Ftail(_eq2_stat_3, _eq2_stat_4, _eq2_stat_2)
	drop if f_test>$Max_Fstat

	save "$Temp_Folder\\ols_results_filtered.dta", replace
	
	cap file close ret_csv
	file open ret_csv using "$Output_Folder\\ret-`yr'-`mon'.csv", write replace
	file write ret_csv "test_begin,test_end,length,portfolio,sp500, asset_weighted,(monthly returns)" _n		
	
	foreach len in 1 5 10 25 50 100 {
		qui use "$Temp_Folder\\ols_results_filtered.dta", clear
		
		qui{
				sort _b_cons 		// rank Alphas from the in-sample period	
				gen rank_bottom = _n
		
				replace _b_cons = _b_cons*(-1)
				sort _b_cons 		// rank Alphas from the in-sample period	
				gen rank_top = _n
				replace _b_cons = _b_cons*(-1)
			}		
			
			preserve 
				qui keep if rank_bottom<=`len' // save the bottom 50 list from in-sample
				qui keep firmid
				qui save "$Temp_Folder\\TrainSetShort`yr'-`mon'-`len'.dta", replace
			restore 

			preserve 
				qui keep if rank_top<=`len' 	// save the top 50 list from in-sample
				qui keep firmid
				qui save "$Temp_Folder\\TrainSetLong`yr'-`mon'-`len'.dta", replace
			restore 	
		
		
			
			qui {
			
				// go back to smaple data
				use "$Temp_Folder\\finalData.dta", replace
				
				keep if postSample==1		// trimmed to post-sample only
				
				// Merge with top 50
				merge m:1 firmid using "$Temp_Folder\\TrainSetShort`yr'-`mon'-`len'.dta"
				gen TopList = _merge==3
				drop _merge
				
				// Merge with bottom 50
				merge m:1 firmid using "$Temp_Folder\\TrainSetLong`yr'-`mon'-`len'.dta"
				gen BottomList = _merge==3
				drop _merge
				
				// Keep only Long/Short portfolio
				keep if TopList==1 | BottomList==1
				
				// Generate adj_ret which equals to the reverse of short firms
				gen adjRet = 0
				replace adjRet =   (exRet + rf) if TopList==1
				replace adjRet = - (exRet + rf) if BottomList==1
				
				// Calculate asset weights
				egen totalMarketCap = total(marketCap)
				gen asset_weights = marketCap/totalMarketCap

				// calculate the cumulative stock returns during the post sample period
				gen lnRet = ln(1+adjRet)
				sort permno date
				by permno: egen cumulativeRetE = total(lnRet)
				gen cumulativeRet = exp(cumulativeRetE) - 1
				drop lnRet cumulativeRetE
				
				// calculate the cumulative s&p 500 returns during the post sample period	
				sum date
				sum sp500 if date==r(max)
				scalar sp500_end = r(mean)
				sum date
				sum sp500 if date==r(min)
				scalar sp500_start = r(mean)
				local cumul_sp500_ret = (sp500_end - sp500_start)/sp500_start
				
				// Collapse to 1 row per firm
				sort permno date
				by permno: gen last = _n==_N
				keep if last==1
				drop last
			
				gen cum_sp500 = `cumul_sp500_ret'
				gen test_begin = TrainSetEnd + 1
				gen test_end	 = TestSetEnd				
				format test_begin %td
				format test_end %td
				sort BottomList
				gen raw_ret = cumulativeRet
				replace raw_ret = - cumulativeRet if BottomList==1
				
				export excel test_begin test_end permno comnam cumulativeRet raw_ret cum_sp500 marketCap asset_weights TopList BottomList ticker primexch using "$Output_Folder\\Portfolio-`yr'-`mon'-`len'.xls", firstrow(variables) replace 	
				* Primary Exchange Code: (N = NYSE, A = NYSE MKT, Q = NASDAQ, R = Arca, X = Other)
			}	
			
			qui sum cumulativeRet [aweight = asset_weights]
			local avgReturn_1 = r(mean)

			file write ret_csv "`test_begin',`test_end',`len',`avgReturn_1',`cumul_sp500_ret', 1" _n		
			qui sum cumulativeRet
			local avgReturn_0 = r(mean)			
			file write ret_csv "`test_begin',`test_end',`len',`avgReturn_0',`cumul_sp500_ret', 0" _n		

			disp "** TestSet Return `yr'-`mon'(`len'):" round(`avgReturn_0'*100, 0.01) "%, or " round(`avgReturn_1'*100, 0.01) "% (weighted); vs S&P 500: " round(`cumul_sp500_ret'*100, 0.01) "%." 
			
			/*
			disp ""
			disp "* Two-Sample t test"
			ttest portRet = benchRet
			local temp = r(p)
			*/
			
			
	}

	
	
	file close _all	
end program

forvalues begin_year = 1999/2012 {
	forvalues begin_month = 1/12 {
		global Start_Year 		= `begin_year'
		global Start_Month 		= `begin_month'
		main
	}
}

exit
























