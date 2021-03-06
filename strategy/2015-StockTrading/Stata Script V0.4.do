* This program is intended to implement the automated stock trading strategy

* Program version 0.3
* Last update Jan/23/2015

clear 														// Leave matrix uncleared
clear mata
macro drop _all
program drop _all
set varabbrev off


****************** Program Settings ******************
global Folder 			= "D:\Dropbox\Projects\2015 - Stock Trading"	// Location of program scripts
global Data 			= "D:\Workspace"								// Location to which temporary files are generated
global DataSource  		= "d:\Workspace\CRSP"							// Location of the original data files (ASCII)
* Variable speicification
global Varlist  		= "fac1 fac2 fac3 fac4 fac5 fac6 fac7 fac8"
*global Varlist  		= "fac1 fac2 fac3 fac4 fac6 fac8"

global RollingWindow  	= "No" 											// "Yes" for the main dataset; "No" for the rolling window simulation
global ShowStats 		= "No" 										// Choose "Yes" or "No"; "Yes" would show all summary statistics during the process (incl. diagrams).
global LoadCRSP 		= "Yes" 										// "Yes" to load the CRSP datasets into a panel dataset
global MonthlyData 		= "No" 										// Convert data from daily to monthly
global UseSP500asRf 	= "No" 										// use S&P 500 as risk free rate
global NumSpecsToRun 	= 1 											// Specify the number of model specifications to run; 1 as default
****************** Rolling Window Specifics **********
// The following Switches are specific to Rolling Window
// Choose "Yes" for RollingWindow to activate the following switches
* Minimum periods per fund
global BeginYear	 	= 2008									// Set the first year for the rolling process to begin with
global SampleWindow 	= 6 									// in MONTHS; Set number of years for extract samples from
global ForecastWindow 	= 1 									// in MONTHS; Set number of years to forecast the model fitness
global MinObsPercentage = 0.7 									// Set the percentage of minimum obsrevations for in-sample and for post-sample period. 
																// For example, 70% implies that if the sample window is 3 years, each fund must at least report 3*12*0.7=25.2 monthly returns during the insample period, and 8.4 months during the post-sample period.
******************************************************

* PROGRAM STARTS HERE *
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
*sysdir set PERSONAL "$Data\ado"
*sysdir set PLUS "$Data\ado\plus"
*sysdir set OLDPLACE "$Data\ado" 
*net set ado PERSONAL
set rmsg on
cd "$Folder"


** Functions

cap program drop change_date
program change_date
	gen date2 = date(date, "YMD")
	format date2 %td
	drop date
	rename date2 date
	order date
	sort date
end program

cap program drop prepare_factors
program prepare_factors
{

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

	keep date rf fac*
	save "D:\Dropbox\Resources\Datasets\Market Factors\factors.dta", replace
}
end program

cap program drop compareList
program compareList
args listLength sorting
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
	disp "* Statistics of Companies in the Current Dataset:"
	qui count
	disp "    - Total Monthly Observations: " r(N)
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
end program	


cap program drop SaveCoefficients
program SaveCoefficients
args mat_name factorname
	cap drop depdt
	gen depdt = exRet
	
	mat `mat_name'_0 = .
	mat `mat_name'_99 = .
	mat `mat_name'_r2 = .
	mat `mat_name'_f = .
	
	forvalues j = 1/9 {
		mat `mat_name'_`j' = .
	}
	if missing("`factorname'") {
	}
	else {
		mat `mat_name'_10 = .
	}	
	forvalues i = 1/$firm_num {
		// In-Sample OLS
		qui regress exRet $Varlist `factorname' if firmid==`i' & inSample==1
		scalar f_test = Ftail(e(df_m), e(df_r), e(F))
		if e(r2)>=0.6 & f_test<=0.1 {
			local decision = "Accepted"
		}
		else {
			local decision = "Rejected"
		}
		
		disp "Spec " $specNum ", firm `i' out of " $firm_num ", r2=" round(e(r2), 0.01) " , f-test Pval: " round(Ftail(e(df_m), e(df_r), e(F)), 0.01) "- `decision'"
		
		mat `mat_name'_r2 = `mat_name'_r2 \ e(r2)
		mat `mat_name'_0 = `mat_name'_0 \ _b[_cons]
		mat `mat_name'_f = `mat_name'_f \ f_test
		
		forvalues j = 1/9 {
			cap mat `mat_name'_`j' = `mat_name'_`j' \ _b[fac`j']
		}
		if missing("`factorname'") {
		}
		else {
			mat `mat_name'_10 = `mat_name'_10 \ _b[`factorname']
		}
		
		/*
		replace dept = 0
		// Post-Sample OLS
		foreach x of global Varlist {
			qui replace depdt = depdt - `x'*_b[`x'] if firmid==`i' & postSample==1
		}
		
		
		if missing("`factorname'") {
		}
		else {
			qui replace depdt = depdt - `factorname'*_b[`factorname'] if firmid==`i' & postSample==1
		}	
		qui regress depdt if firmid==`i' & postSample==1
		
		mat `mat_name'_99 = `mat_name'_99 \ _b[_cons]	
		*/
	}
	cap drop depdt
	
	global specNum = $specNum + 1
end program

cap program drop CoefficientMatrix
program CoefficientMatrix
args matname ithvar
* Note 0 means the intercept term - "Alpha"
	mat `matname' = .
	forvalues i = 1/$firm_num {
		mat `matname' = `matname' \ `i'
	}	
	mat ProductRef = .
	forvalues i = 1/$firm_num {
		cap sum permno if firmid==`i'
		disp "i is `i'"
		mat ProductRef = ProductRef \ r(mean)
	}
	
if $NumSpecsToRun==1 {
	if `ithvar'<=9 | `ithvar'==99 {
		mat `matname' = `matname' , ProductRef, C1_`ithvar' 
		global Varname = "firmID permno DefaultModel"
	}
	if `ithvar'==10 {
		mat `matname' = `matname' , ProductRef , C1_`ithvar' 
		global Varname = "firmID permno DefaultModel"	
	}
}
else {
	
	if `ithvar'<=9 | `ithvar'==99 {
		mat `matname' = `matname' , ProductRef, A_`ithvar' , B1_`ithvar' , B2_`ithvar' , C1_`ithvar' , C2_`ithvar' , D1_`ithvar' , D2_`ithvar'
		global Varname = "firmID permno Non_Inclusion Non_Orth_EW Non_Orth_VW Orth_Alpha_EW Orth_Alpha_VW Orth_NoAlpha_EW Orth_NoAlpha_VW"
	}
	if `ithvar'==10 {
		mat `matname' = `matname' , ProductRef , B1_`ithvar' , B2_`ithvar' , C1_`ithvar' , C2_`ithvar' , D1_`ithvar' , D2_`ithvar'
		global Varname = "firmID permno Non_Orth_EW Non_Orth_VW Orth_Alpha_EW Orth_Alpha_VW Orth_NoAlpha_EW Orth_NoAlpha_VW"	
	}
}
	mat `matname' = `matname'[2..rowsof(`matname'), 1...]

	mat colnames `matname' = $Varname
	preserve
		clear
		svmat `matname'
		local j = 1
		foreach x of global Varname {
			disp "`x'"
			rename `matname'`j' `x'
			local j = `j' + 1
		}
		save "$Data\\Sample_`matname'_`ithvar'.dta", replace
	restore
end program	

/*

* Main Program
cap program drop RollingWindow
program RollingWindow
args bYr sWin fWin
*/
*** Temporary
	local bYr = $BeginYear
	local sWin = $SampleWindow
	local fWin = $ForecastWindow
	
***

	// Reset variables
	scalar firstDay=-1
	global specNum = 1
	global beginYear = `bYr'
	global sampleWindow = `sWin'
	global forecastWindow = `fWin'
	
	
	cap file close table1
	file open table1 using "$Folder\\Results\\WYrs-$sampleWindow-FYrs-$forecastWindow-$beginYear-Table1ReturnsByCategory.csv", write replace
	file write table1 "Summary: Cross-Sectional (Note: Start means the beginning of in-sample period; end means the end of in-sample period)" _n	
	file write table1 "Industry, # Firms Start, % in Total Firms Start, # Firms End, % in Total Firms End, Avg Size Start, Avg Size End" _n
	
	cap file close table2
	file open table2 using "$Folder\\Results\\WYrs-$sampleWindow-FYrs-$forecastWindow-$beginYear-Table2TimeSeriesStats.csv", write replace
	file write table2 "Summary: Time Series Data Summary" _n	
	file write table2 "Industry, Month, # Firms Total, # Firms, Avg Size, Equal Weighted Excess Return Mean, EW Ret Std, EW Ret Skewness, EW Ret Kurtosis, Value Weighted Excess Return Mean, VW Ret Std, VW Ret Skewness, VW Ret Kurtosis" _n
	
	cap file close table4
	file open table4 using "$Folder\\Results\\Table4RollingWindow.csv", write replace
	
	cap file close tableRoll
	file open tableRoll using "$Folder\\Results\\Rwin-$sampleWindow-Fyrs-$forecastWindow-$beginYear.csv", write replace
	file write tableRoll "Summary Statistics of Rolling Window" _n	
	local temp1 = $beginYear
	local temp2 = $beginYear + $sampleWindow
	file write tableRoll "Sampe period, `temp1' - `temp2'" _n	
	local temp1 = $beginYear + $sampleWindow + 1
	local temp2 = $beginYear + $sampleWindow + $forecastWindow
	file write tableRoll "Forecast period, `temp1' - `temp2'" _n
	
	global totalWindow = $sampleWindow + $forecastWindow
	global minTimeSpan  = $sampleWindow*$MinObsPercentage 		// In Sample Period, funds with less than this number of periods being observed in the sample will be dropped
	global minTime_Post = $forecastWindow*$MinObsPercentage 		// In Post-Sample Period, funds with less than this number of periods being observed in the sample will be dropped
		
	/*
	if "$RollingWindow"=="No" {
		global minTimeSpan  = 36
		global minTime_Post = 36
			
	}
	*/

	disp "*******************************************************"		
	disp " S1. Prepare Dataset "
	disp "*******************************************************"	
	*S1.1 Load data from Lippers Tass
		if "$LoadCRSP"=="Yes" {
			clear
			local endYr = `bYr' + round(`sWin'/12 - 0.51) + 1 + round(`fWin'/12 - 0.51) + 1

			forvalues yr = `bYr'/`endYr' {
				append using "$DataSource\\`yr'.dta"
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

		//Declare time series
		xtset permno date
		
		// Generate month variable staring with 1
		cap drop month
		gen month = mofd(date)
		qui sum month
		local small = r(min)	
		replace month = month - `small' + 1
		
		save "$Data\\CRSP-$beginYear-$endYear.dta", replace
		
	*S1.3 Merge with factor variables
		 
		// Prepare 9 factors
		/*
		use "D:\Dropbox\Resources\Datasets\Lippers Tass\Factor.dta", clear
		// Declare time series
		gen double month = monthly(time, "YM")
		replace month = month - `small' + 1
		drop time
		save "$Data\\Factors.dta", replace
		*/
		*prepare_factors
		
		
		use "$Data\\CRSP-$beginYear-$endYear.dta", clear
		
		merge m:1 date using "D:\\Dropbox\\Resources\\Datasets\\Market Factors\\factors.dta"
		drop if _merge==2
		drop _merge
		
	*S1.4 Generate some variables
		// define excess return at t
		if "$UseSP500asRf"=="Yes" {
			gen exRet = ret - sp500
		}
		else {
			gen exRet = ret - rf 		
		}
		// Generate time variables
		gen yr 		= year(date)
		gen mon 	= month(date)
		gen mon_ 	= mofd(date)
		
		// Find the sample window
		if firstDay==-1 {
			scalar firstDay = mdy(01, 01, $beginYear)
		}
		
		scalar windowStartMonth = mofd(firstDay)
		scalar windowEndMonth = windowStartMonth + $totalWindow
		
		keep if mon_<=windowEndMonth & mon_>=windowStartMonth
		drop mon_
		
		scalar cutOffDay = dofm(mofd(firstDay) + $sampleWindow + 1)
		
		
		// Identify in-sample observations
		gen inSample = 0
		replace inSample = date<cutOffDay 	

		// post-sample observations
		gen postSample = 0
		replace postSample = date>=cutOffDay
		

		
		tostring siccd, replace
		gen naicsMajor = substr(siccd, 1, 1)
	/*
		drop if naicsMajor=="11" | naicsMajor=="23" | naicsMajor=="49" | ///
				naicsMajor=="53" | naicsMajor=="55" | naicsMajor=="56" | ///
				naicsMajor=="61" | naicsMajor=="62" | naicsMajor=="71" | ///
				naicsMajor=="72" | naicsMajor=="82" | naicsMajor=="92" | ///
				naicsMajor=="81"
				*/
		tab naicsMajor
		drop if naicsMajor=="."
		drop if naicsMajor=="9"
		
		encode naicsMajor, generate(category)	
		
		sort permno month date
		
		disp "Dataset successfully loaded"
		
		save "$Data\\Panel.dta", replace 		
		}

	disp "*******************************************************"		
	disp " S2. Impute Estimated Market Cap "
	disp "*******************************************************"			
		use "$Data\\Panel.dta", clear
	*S2.1 Generate some variables to access the proportion of data in which the estiamted assets are missing
		sort permno month date
		by permno: gen countByMonth = _n
		by permno: egen fundObs = max(countByMonth)
	
		// gen market cap
		gen marketCap = shrout*1000 * prc
		
		disp "If Market Cap is zero, they are replaced to missing"
		replace marketCap=. if marketCap==0
		
		gen missingAsset = 0
		replace missingAsset = 1 if marketCap==.
		by permno: egen totalMissingAsset = total(missingAsset)
		gen noMissingAsset = totalMissingAsset==0
		gen someMissingAsset = totalMissingAsset>0 & totalMissingAsset<fundObs
		gen allMissingAsset = totalMissingAsset==fundObs
		
		tabstat noMissingAsset someMissingAsset allMissingAsset, stat(n mean sd min max) col(stat) varwidth(16)
				
		// No missing observations
		
	*S2.2 Calcualte weighted average returns on assets
		sort month date
		by month: egen totalMarketCap = total(marketCap)

		gen assetWeights = marketCap/totalMarketCap
		gen monthReturns = assetWeights*ret

		sort permno month date
		drop missingAsset totalMissingAsset noMissingAsset someMissingAsset allMissingAsset
						
	disp "*******************************************************"		
	disp " S3. Generating Some Variables "
	disp "*******************************************************"		
	disp " "
		disp "* The sample consists of the following years: "
		tab yr		
		disp " "
		disp "    - The cut-off date is : Year " year(cutOffDay) ", Month " month(cutOffDay)
		disp ""
		disp "    - The number of in-sample observations is: "
		tab inSample	
		disp ""
		disp "    - The number of out-of-sample observations is"
		tab postSample				
		
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

		if "$ShowStats"=="Yes" {
				*ShowStat
				
				
				// Prepare Table 1: Cross sectional stats
				sum month if inSample==1
				local beginMonthInSample = r(min)
				local endMonthInSample = r(max)
				
				tab category
				local cat_num = r(r) 
				
				forvalues i = 1/`cat_num' {
					// Count total firms at the begining of in-sample
					count if month==`beginMonthInSample'
					local totalfirmNum = r(N)
					
					// Count categorical firms at the beginning of in-sample
					count if category==`i' & month==`beginMonthInSample'
					local categoryfirmNum = r(N)
					
					local percentBegin = `categoryfirmNum' / `totalfirmNum'
							
					sum marketCap if category==`i' & month==`beginMonthInSample'
					local avgSizeStart = r(mean)
							
					// Count total firms at the end of in-sample
					count if month==`endMonthInSample'
					local totalfirmNumEnd = r(N)
					
					// Count categorical firms at the end of in-sample
					count if category==`i' & month==`endMonthInSample'
					local categoryfirmNumEnd = r(N)
					
					local percentEnd = `categoryfirmNumEnd' / `totalfirmNumEnd'
						
					sum marketCap if category==`i' & month==`endMonthInSample'
					local avgSizeEnd = r(mean)
					
					// Write into files
					file write table1 "`i', `categoryfirmNum', `percentBegin', `categoryfirmNumEnd', `percentEnd', `avgSizeStart', `avgSizeEnd'" _n
				}
				file close table1
				
				
				// Prepare Table 2: Time series stats
				sum month if inSample==1
				local beginMonthInSample = r(min)
				local endMonthInSample = r(max)
				
				sort category month date
				gen vwNumer = exRet*marketCap
				by category month: egen vwDenom = total(marketCap)
				gen vwRet = vwNumer/vwDenom	
				
				tab category
				local cat_num = r(r) 
				
				forvalues i = 1/`cat_num' {
						// Count total firms 
						count
						local totalfirmNum = r(N)
						
						// Count categorical firms
						count if category==`i'
						local categoryfirmNum = r(N)
						
						sum marketCap if category==`i'
						local avgSize = r(mean)
							
						// Equally weighted excess return
						sum exRet if category==`i', detail
						
						local ewMean = r(mean)
						local ewStd = r(sd)
						local ewSkew = r(skewness)
						local ewKurt = r(kurtosis)
						
						// Value weighted excess return
						sum vwRet if category==`i', detail
						
						local vwMean = r(mean)
						local vwStd = r(sd)
						local vwSkew = r(skewness)
						local vwKurt = r(kurtosis)					
						
						// Write into files
						file write table2 "`i', all months, `totalfirmNum', `categoryfirmNum', `avgSize', `ewMean', `ewStd', `ewSkew', `ewKurt', `vwMean', `vwStd', `vwSkew', `vwKurt' " _n
				
				
				}
				
				forvalues i = 1/`cat_num' {
					forvalues m = `beginMonthInSample'/`endMonthInSample' {
						// Count total firms for each month
						count if month==`m'
						local totalfirmNum = r(N)
						
						// Count categorical firms for each month
						count if category==`i' & month==`m'
						local categoryfirmNum = r(N)
						
						sum marketCap if category==`i' & month==`m'
						local avgSize = r(mean)
							
						// Equally weighted excess return
						sum exRet if category==`i' & month==`m', detail
						
						local ewMean = r(mean)
						local ewStd = r(sd)
						local ewSkew = r(skewness)
						local ewKurt = r(kurtosis)
						
						// Value weighted excess return
						sum vwRet if category==`i' & month==`m', detail
						
						local vwMean = r(mean)
						local vwStd = r(sd)
						local vwSkew = r(skewness)
						local vwKurt = r(kurtosis)					
						
						// Write into files
						file write table2 "`i', `m', `totalfirmNum', `categoryfirmNum', `avgSize', `ewMean', `ewStd', `ewSkew', `ewKurt', `vwMean', `vwStd', `vwSkew', `vwKurt' " _n
					}
				
				}
				file close table2			
				drop vwNumer vwDenom vwRet			
		}		
		
	*S3.4 Generate some more variables
		sort permno month date
		cap drop countByMonth
		cap drop fundObs
		by permno: gen countByMonth = _n
		by permno: egen firmObs = max(countByMonth)
		// Count the number of observations for each firm
		by permno: egen sumRet = total(ret)
		by permno: gen meanRet = sumRet/firmObs
		drop firmObs countByMonth 
		
		if "$ShowStats"=="Yes" {	
			
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

		}
		
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
		
		if "$ShowStats"=="Yes" {	
		
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
disp " S4. Prepare Final Sample Dataset after Dropping Observations "
disp "*******************************************************"	
	disp "* S4.1. Dropping observations s.t. criteria"
		disp "* Drop firms with too few observations in In-Sample Period"
		qui {
			sort permno month date
			by permno: gen periods_temp = _n
			replace periods_temp = 0 if inSample==0
			by permno: egen periods = max(periods_temp)
		}
		firmCount
		local temp1 = $firmNumber 
		drop if periods<$minTimeSpan
		firmCount
		local temp2 = `temp1' - $firmNumber
		disp "# firms excluded due to too few obs in sample, `temp2'" _n	

		file write tableRoll  "# firms excluded due to too few obs in sample, `temp2'" _n	
		drop periods_temp periods	

		disp "* Drop firms with too few observations in Post-Sample Period"
		qui {
			gen month_i = - month
			sort permno month_i
			bysort permno: gen periods_temp = _n
			replace periods_temp = 0 if postSample==0
			bysort permno: egen periods = max(periods_temp)
			sum periods
		}
		firmCount
		local temp1 = $firmNumber 		
		drop if periods<$minTime_Post
		firmCount
		local temp2 = `temp1' - $firmNumber
		disp "# firms excluded due to too few obs in postsample, `temp2'" _n		
		drop periods_temp periods month_i
		qui sort permno month date

		
		disp "* Drop firms if category is Undefined"
		firmCount
		local temp1 = $firmNumber 		
		drop if category==.
		local temp2 = `temp1' - $firmNumber
		disp "# firms excluded due to undefined category, `temp2'" _n		
		file write tableRoll  "# firms excluded due to undefined category, `temp2'" _n		

		
		disp "* Drop obs if any missing values in the factors"
		firmCount
		local temp1 = $firmNumber 			
		drop if exRet==.
		foreach x of global Varlist {
			drop if `x'==.
		}
		local temp2 = `temp1' - $firmNumber
		disp "# firms excluded due to missing values, `temp2'" _n		
		file write tableRoll "# firms excluded due to missing values, `temp2'" _n		
			
		disp ""
		disp "* Check again sample size for each firm"
		disp "    Note: no observations should be dropped below"
		qui gen fail = 0
		qui replace fail = 1 if inSample==1 & ( exRet==. | fac1==. | fac2==. | fac3==. | fac4==. | fac5==. | fac6==. | fac7==. | fac8==. | fac9==. )
		qui replace fail = 1 if postSample==1 & ( exRet==. | fac1==. | fac2==. | fac3==. | fac4==. | fac5==. | fac6==. | fac7==. | fac8==. | fac9==. )

		sort permno month date 
		qui by permno: egen _fail = max(fail)
		drop if _fail==1
		drop fail _fail

	disp "* Some category may have estiamted assets equal to zero. "
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
	drop category
	encode naicsMajor, generate(category)	
	
	disp "* S4.2. Calculate EW and VW index"
	*S4.2a Equal-weighted Index (Un-Orthogonalised); Eq. (1)
		preserve
			// Count number of firms per Primary Category
			sort category month date
			
			by category month: gen count_temp = _n
			by category month: egen count_cat = max(count_temp)
			
			// gen sum of excess returns - numerator
			sort category month date
			by category month: egen numer = sum(exRet)

			gen eb_ew = numer/count_cat

			keep eb_ew category date month inSample postSample
			duplicates drop
			save "$Data\\Panel_EW.dta", replace
				
			
				
			merge m:1 month using "$Data\\Factors.dta"
			drop if _merge==2
			drop _merge
		
			tab category
			local cat_num = r(r) 
	
			gen eb_ew_o1 = .
			gen eb_ew_o2 = .
			
			save "$Data\\temp.dta", replace
			
			// EWO In Sample
			use "$Data\\temp.dta", clear
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
			keep date month category eb_ew eb_ew_o1 eb_ew_o2 inSample
			save "$Data\\inSample_EWO.dta", replace
			
			// EWO Post Sample
			use "$Data\\temp.dta", clear
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
			keep date month category eb_ew eb_ew_o1 eb_ew_o2 postSample
			save "$Data\\postSample_EWO.dta", replace
		restore

	*S4.2b Value-weighted Index; Eq. (2)
		preserve
			cap drop numer
			cap drop denom
			
			bysort category month date: egen numer = total(exRet*marketCap)
					
			// Count number of firms per Primary Category
			bysort category month date: egen denom = total(marketCap)
			gen eb_vw = numer/denom

			keep eb_vw category date month inSample postSample
			duplicates drop
			save "$Data\\Panel_VW.dta", replace
			
			merge m:1 month using "$Data\\Factors.dta"
			drop if _merge==2
			drop _merge

			gen eb_vw_o1 = .
			gen eb_vw_o2 = .		
			
			save "$Data\\temp.dta", replace
			
			// VWO In Sample
			use "$Data\\temp.dta", clear		
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
			keep date month category eb_vw eb_vw_o1 eb_vw_o2 inSample
			save "$Data\\inSample_VWO.dta", replace		
			
			// VWO Post Sample
			use "$Data\\temp.dta", clear				
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
			keep date month category eb_vw eb_vw_o1 eb_vw_o2 postSample
			save "$Data\\postSample_VWO.dta", replace		
		restore		
		
	disp "* S4.3. Descriptive Statistics of the Final Sample Dataset"
	
	disp ""
	firmCount
	local temp2 = $firmNumber
	file write tableRoll "# firms in Final Data, `temp2'" _n		
	disp ""
	cap log close


	save "$Data\\SampleData.dta", replace
	
disp "*******************************************************"	
disp " S4. OLS Regressions "
disp "*******************************************************"	
	use "$Data\\SampleData.dta", clear
	* Model specifications
	* a. Non-inclusion of any peer group benchmark (?o EB?, corresponding to equa-tion (4).
	* b. Inclusion of a non-orthogonalized peer group benchmark (?B non-ortho.?
	* c. Inclusion of an orthogonalized peer group benchmark ?Use of epsilons e plus benchmark-alphas a (?B = a+e?, i.e., corresponding to equation (12).
	* d. Inclusion of an orthogonalized peer group benchmark without the benchmark-alphas ?Use of the epsilons e only (?B = e?, i.e., corresponding to equation (13).
	
	*S5.1 Prepare Data
		merge m:1 date month category inSample using "$Data\\inSample_EWO.dta"
		drop _merge
		ChangeVarNames
		merge m:1 date month category inSample using "$Data\\inSample_VWO.dta"
		drop _merge
		ChangeVarNames
		merge m:1 date month category postSample using "$Data\\postSample_EWO.dta"
		drop _merge
		ChangeVarNames
		merge m:1 date month category postSample using "$Data\\postSample_VWO.dta"
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
		replace fail = 1 if inSample==1 & ( exRet==. | fac1==. | fac2==. | fac3==. | fac4==. | fac5==. | fac6==. | fac7==. | fac8==. | fac9==. )
		replace fail = 1 if postSample==1 & ( exRet==. | fac1==. | fac2==. | fac3==. | fac4==. | fac5==. | fac6==. | fac7==. | fac8==. | fac9==. )

		sort permno month date
		by permno: egen _fail = max(fail)
		drop if _fail==1
		drop fail _fail

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

		save "$Data\\finalData.dta", replace
		keep if inSample==1
		statsby _b e(r2) e(F) e(df_m) e(df_r) _se, by(firmid) verbose clear: regress exRet $Varlist eb_ew_o1 

		save "$Data\\ols_results.dta", replace

		
disp "*******************************************************"	
disp " S5. Model Fittness "
disp "*******************************************************"	
		use "$Data\\ols_results.dta", clear
		
		* Exclude if r2 is too low
		drop if _eq2_stat_1<0.6
		* Exclude if F-stats is too low
		gen f_test = Ftail(_eq2_stat_3, _eq2_stat_4, _eq2_stat_2)
		drop if f_test>0.1


/*		
		// Produce pairwise correlations
		file write tableRoll "Fitness Stats - Pairwise Correlation" _n				
		local i = 1
		foreach x of global VarName {

			qui corr `x'*
			local temp = r(rho)

			disp "    - Spec `i' Correlation is: " r(rho) "; Spec Detail: `x'"
			
			file write tableRoll "Spec `x', `temp'" _n				
			
			local i = `i' + 1
		}

	
	disp "S5.2 Compare the top 10 rankings "
	disp "    Note: Number of firms that appears in both Top 10 list from in-sample and post-sample"

		disp ""
		disp "    - Top 100 Ranking"
		file write tableRoll "Fitness Stats - Top 100 Ranking" _n				
		compareList 100 -1 		// the first parameter is the length of list i.e. Top 100; 
								// the second parameter is the sorting, 1 for Bottom, -1 for Top; 

		disp ""
		disp "    - Top 50 Ranking"		
		file write tableRoll "Fitness Stats - Top 50 Ranking" _n	
		compareList 50 -1 			
		disp ""
		disp "    - Top 10 Ranking"	
		file write tableRoll "Fitness Stats - Top 10 Ranking" _n	
		compareList 10 -1 

		disp ""
		disp "    - Bottom 100 Ranking"	
		file write tableRoll "Fitness Stats - Bottom 100 Ranking" _n	
		compareList 100 1 		// the first parameter is the length of list i.e. Top 100; 
								// the second parameter is the sorting, 1 for Bottom, -1 for Top; 
		disp ""
		disp "    - Bottom 50 Ranking"		
		file write tableRoll "Fitness Stats - Bottom 50 Ranking" _n	
		compareList 50 1 		
		disp ""
		disp "    - Bottom 10 Ranking"	
		file write tableRoll "Fitness Stats - Bottom 10 Ranking" _n	
		compareList 10 1 
	
	
	disp ""
	disp "S5.3 Calculate MAD of rank differences"
	cap log close
	file write tableRoll "Fitness Stats - MAD of Rank Differences" _n	
	preserve
		local i = 1
		foreach x of global VarName {
			qui{
					replace `x'_s = `x'_s*(-1)
					sort `x'_s 		// rank Alphas from the in-sample period	
					cap drop rank_`x'_s
					gen rank_`x'_s = _n
					replace `x'_p = `x'_p*(-1)
					sort `x'_p 		// rank Alphas from the post-sample period	
					cap drop rank_`x'_p
					gen rank_`x'_p = _n
								
					sort firmID
					cap drop diff
					gen diff = abs(rank_`x'_s - rank_`x'_p)
					
					sum diff
				}
			
			disp "    - Spec `i' Mean Absolute Deviation is :" r(mean) ", using specification `x'"
			local temp = r(mean)
			file write tableRoll "Spec `x', `temp'" _n	
			local i = `i' + 1
		}
	restore
	
	
	disp ""
	disp "S5.4 Wilcoxon Signed-Rank Test"
	cap log close
	file write tableRoll "Fitness Stats - Wilcoxon Signed-Rank Test (z-stats)" _n
	
	preserve
		local i = 1
		foreach x of global VarName {
			qui{
					replace `x'_s = `x'_s*(-1)
					sort `x'_s 		// rank Alphas from the in-sample period	
					cap drop rank_`x'_s
					gen rank_`x'_s = _n
					replace `x'_p = `x'_p*(-1)
					sort `x'_p 		// rank Alphas from the post-sample period	
					cap drop rank_`x'_p
					gen rank_`x'_p = _n
				}		
			disp ""
			disp "    - `i'. Specification `x': Wilcoxon Signed-Rank Test Result:"
			disp "    - `i'. Specification `x': Wilcoxon Signed-Rank Test Result:"
			signrank rank_`x'_s = rank_`x'_p
			local temp = r(z)
			file write tableRoll "Spec `x', `temp'" _n				
			
			local i = `i' + 1
		}	
	restore
	
	disp ""
	disp "S5.5 Portfolio Performance"
	disp "    Note: This portfolio long, i.e., the top 50 Hedge firms,"
	disp " 			while short the bottom 50 Hedge firms."
	disp "			The performance is then compared to benchmark of Equally-Weighted Portfolio of all available firms during the period."
	
	file write tableRoll "Fitness Stats - Long/Short Portfolio Performance (annualised excess return)" _n
*/
	save "$Data\\temp.dta", replace 
	
	
	foreach len in 10 25 50 100 {
		use "$Data\\temp.dta", clear
		*file write tableRoll "Long/Short Portfolio = Long Top `len' firms & Short Bottom `len' firms" _n

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
				qui save "$Data\\InSample-Buttom`len'.dta", replace
			restore 

			preserve 
				qui keep if rank_top<=`len' 	// save the top 50 list from in-sample
				qui keep firmid
				qui save "$Data\\InSample-Top`len'.dta", replace
			restore 	
		
		
			preserve
			qui {
			
				// go back to smaple data
				use "$Data\\finalData.dta", replace
				
				keep if postSample==1		// trimmed to post-sample only
				
				// Merge with top 50
				merge m:1 firmid using "$Data\\InSample-Top`len'.dta"
				gen TopList = _merge==3
				drop _merge
				
				// Merge with bottom 50
				merge m:1 firmid using "$Data\\InSample-Buttom`len'.dta"
				gen BottomList = _merge==3
				drop _merge
				
				
				// Keep only Long/Short portfolio
				keep if TopList==1 | BottomList==1
				
				// Generate adj_ret which equals to the reverse of short firms
				gen adjRet = 0
				replace adjRet =   ret if TopList==1
				replace adjRet = - ret if BottomList==1
				
		
				// calculate the cumulative stock returns during the post sample period
				gen lnRet = ln(1+adjRet)
				sort permno date
				by permno: egen cumulativeRetE = total(lnRet)
				gen cumulativeRet = exp(cumulativeRetE) - 1
				drop lnRet cumulativeRetE
				
				// Collapse to 1 row per firm
				sort permno date
				by permno: gen last = _n==_N
				keep if last==1
				drop last
				
				sum yr
				local yr = r(mean)
				sum mon
				local mon = r(mean)
				
				sum cumulativeRet
				local avgReturn = round(((1+r(mean))^(365/`len') - 1)*100, 0.01)
				
				sum sp500
				local sp500 = round(((1+r(mean))^(12) - 1)*100, 0.01)
								
			}
				disp ""
				disp "* Spec: `x' len(`len'), TestSet `yr'-`mon': `avgReturn'% p.a., v.s. S&P 500: `sp500'% p.a." 

				/*
				disp ""
				disp "* Two-Sample t test"
				ttest portRet = benchRet
				local temp = r(p)
				*/
			restore
			
	}

	
	
file close _all	
exit
end Program
		
		
/*

if "$RollingWindow" == "Yes" {
	forvalues year = 1995/2008 {
		RollingWindow `year' $SampleWindow $ForecastWindow
	}
}
else {
	global BeginYear	 	= 1990									// Set the first year for the rolling process to begin with
	global SampleWindow 	= 17 									// Set number of years for extract samples from
	global ForecastWindow 	= 6 									// Set number of years to forecast the model fitness
	
	// in line 288 there are some other settings
	local minTimeSpan  = 36
	local minTime_Post = 36

	RollingWindow 1990 $SampleWindow $ForecastWindow
}

				
