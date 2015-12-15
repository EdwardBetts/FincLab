/* 	This program is associated with "Merging data fetched by the eBay fetch bot"
*/
	
* Program Version 1.1
* Last update 25/June/2014

clear 														// Leave matrix uncleared
clear mata
macro drop _all
program drop _all
set varabbrev off

******************************************************
******************  Rolling-window  ******************
******************************************************
****************** Program Settings ******************
global outputFolder	= "D:\Workspace\Outputs\" 				// Folder to save the merged dataset
global asset_weighted = 0
global since_2000 	= "Yes"
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

clear



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

* Import Fama French Factors
import delimited "D:\Dropbox\Resources\Datasets\Market Factors\F-F_Research_Data_Factors_daily.txt", delimiter(space, collapse) clear
tostring date, replace
change_date
// collapse to monthly date
gen time = mofd(date)
sort time date
by time: gen last = _n==_N
keep if last==1
// gen monthly returns
tsset time
drop date last
keep time rf
save "$outputFolder\\series_rf.dta", replace 


* Import S&P500 series	
import delimited "D:\Dropbox\Resources\Datasets\Market Factors\S&P500.csv", delimiter(comma) clear 
change_date
keep date adjclose
rename adjclose sp500
// collapse to monthly date
gen time = mofd(date)
sort time date
by time: gen last = _n==_N
keep if last==1
// gen monthly returns
tsset time
drop date last
gen sp500_ret = D.sp500/L.sp500
save "$outputFolder\\sp500_prices.dta", replace 

clear

* Prepare result data	
local myfiles: dir "$outputFolder\\" files "ret*.csv"
foreach x of local myfiles {
	preserve
		import delimited "$outputFolder\\`x'", delimiter(",", asstring) bindquote(nobind) varnames(1) stripquote(no) case(preserve) clear 
		tempfile temp_file
		save `temp_file'
	restore
	append using `temp_file'
	
}

format test_begin %td
format test_end %td

cap rename month length
cap rename porfolio portfolio
drop monthlyret*

gen mon = mofd(test_end)

format mon %tm
if "$since_2000"=="Yes" {
	gen yr_2000 = mofd(mdy(01, 01, 2000))
	format yr_2000 %tm
	order mon yr_2000
	drop if mon<yr_2000
	drop yr_2000
}

sort asset_weighted length mon




// calculate the cumulative stock returns
gen lnRet = ln(1 + portfolio)
by asset_weighted length: gen cumulativeRetE = sum(lnRet)
gen ret_index = exp(cumulativeRetE)*100
drop cumulativeRetE lnRet

* Plot cumulative returns 
keep if asset_weighted==$asset_weighted
drop test_begin mon asset_weighted
reshape wide portfolio sp500 ret_index, i(test_end) j(length)

// calculate the cumulative S&P500 returns
gen time = mofd(test_end)
tsset time, monthly



merge 1:1 time using "$outputFolder\\sp500_prices.dta"
drop if _merge==2
drop _merge

merge 1:1 time using "$outputFolder\\series_rf.dta"
drop if _merge==2
drop _merge

gen lnSP500Ret2 = ln(1 + sp500_ret)
gen cumulativeRetE = sum(lnSP500Ret2)
gen ret_sp500_2 = exp(cumulativeRetE)*100
drop cumulativeRetE lnSP500Ret2
 
* Output metrics for portfolio performance
// Absolute return
order time
disp "Time Period: " year(dofm(time[1])) "-" month(dofm(time[1])) " to " year(dofm(time[_N])) "-" month(dofm(time[_N]))
disp "Absolute Return in S&P500: " (sp500[_N] - sp500[1])/sp500[1]*100 "%, or " ((sp500[_N]/sp500[1])^(12/(time[_N]-time[1]+1))-1)*100 "% p.a."
foreach len in 1 5 10 25 50 100 {
	disp "Absolute Return from Portfolio (`len'): " (ret_index`len'[_N] - ret_index`len'[1])/ret_index`len'[1]*100 "%, or " ((ret_index`len'[_N]/ret_index`len'[1])^(12/(time[_N]-time[1]+1))-1)*100 "% p.a."
}				

// Volatility
disp "Time Period: " year(dofm(time[1])) "-" month(dofm(time[1])) " to " year(dofm(time[_N])) "-" month(dofm(time[_N]))
qui sum sp500_ret
local sp500_sd = r(sd)*sqrt(12)
disp "Volatility in S&P500: " `sp500_sd' " p.a."
foreach len in 1 5 10 25 50 100 {
	qui sum portfolio`len'
	local port = r(sd)*sqrt(12)	
	disp "Volatility of Portfolio (`len'): " `port' " p.a., or " (`port' - `sp500_sd')/`sp500_sd'*100 "% of S&P 500's volatility"
}				

// Sharpe Ratio
gen sp500_excess_ret = sp500_ret - rf
qui sum sp500_excess_ret
local sp500_sharpe = r(mean)/r(sd)
disp "Sharpe Ratio of S&P500: " `sp500_sharpe'
foreach len in 1 5 10 25 50 100 {
	qui gen port_excess_ret = portfolio`len' - rf
	qui sum port_excess_ret
	local port = r(sd)*sqrt(12)	
	disp "Sharpe Ratio of Portfolio (`len'): " `port' ", or " (`port' - `sp500_sharpe')/`sp500_sharpe'*100 "% of S&P 500's sharpe ratio"
	drop port_excess_ret
}	
drop sp500_excess_ret
	
// Correlation with S&P 500
corr portfolio? portfolio?? portfolio??? sp500_ret
* Graphs
rename ret_sp500_2 SP500
foreach len in 1 5 10 25 50 100 {
	rename ret_index`len' Strategy`len'
	label variable Strategy`len' "Long/Short `len' Stocks"
}


foreach len in 1 5 10 25 50 100 {
	twoway  ///
	(tsline SP500, lcolor(green) lwidth(thick)) ///
	(tsline Strategy`len', lcolor(blue) lwidth(thick)) , ///
	ytitle(Cumulative Index (2000m1 = 100)) ///
	ylabel(, labels angle(horizontal) ticks grid) ///
	ymtick(##2, labels angle(horizontal) valuelabel) ///
	ttitle("") ///
	tlabel(#5, labels angle(horizontal)) ///
	title(Long/Short `len' Stocks v.s. S&P 500)  ///
	legend(on position(11) ring(0) rows(2) color(none) rowgap(zero) colgap(zero) keygap(zero) size(small) margin(small) nobox linegap(small) region(margin(tiny) lcolor(none) lwidth(none)) bmargin(tiny)) ///
	name(g`len', replace)
}
///	legend(on position(7) ring(0)) ///

graph combine g5 g10 g25 g100


	
