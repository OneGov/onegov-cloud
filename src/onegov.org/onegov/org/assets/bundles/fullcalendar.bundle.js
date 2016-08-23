(function(global,factory){typeof exports==='object'&&typeof module!=='undefined'?module.exports=factory():typeof define==='function'&&define.amd?define(factory):global.moment=factory()}(this,function(){'use strict';var hookCallback;function utils_hooks__hooks(){return hookCallback.apply(null,arguments);}
function setHookCallback(callback){hookCallback=callback;}
function isArray(input){return Object.prototype.toString.call(input)==='[object Array]';}
function isDate(input){return input instanceof Date||Object.prototype.toString.call(input)==='[object Date]';}
function map(arr,fn){var res=[],i;for(i=0;i<arr.length;++i){res.push(fn(arr[i],i));}
return res;}
function hasOwnProp(a,b){return Object.prototype.hasOwnProperty.call(a,b);}
function extend(a,b){for(var i in b){if(hasOwnProp(b,i)){a[i]=b[i];}}
if(hasOwnProp(b,'toString')){a.toString=b.toString;}
if(hasOwnProp(b,'valueOf')){a.valueOf=b.valueOf;}
return a;}
function create_utc__createUTC(input,format,locale,strict){return createLocalOrUTC(input,format,locale,strict,true).utc();}
function defaultParsingFlags(){return{empty:false,unusedTokens:[],unusedInput:[],overflow:-2,charsLeftOver:0,nullInput:false,invalidMonth:null,invalidFormat:false,userInvalidated:false,iso:false};}
function getParsingFlags(m){if(m._pf==null){m._pf=defaultParsingFlags();}
return m._pf;}
function valid__isValid(m){if(m._isValid==null){var flags=getParsingFlags(m);m._isValid=!isNaN(m._d.getTime())&&flags.overflow<0&&!flags.empty&&!flags.invalidMonth&&!flags.invalidWeekday&&!flags.nullInput&&!flags.invalidFormat&&!flags.userInvalidated;if(m._strict){m._isValid=m._isValid&&flags.charsLeftOver===0&&flags.unusedTokens.length===0&&flags.bigHour===undefined;}}
return m._isValid;}
function valid__createInvalid(flags){var m=create_utc__createUTC(NaN);if(flags!=null){extend(getParsingFlags(m),flags);}
else{getParsingFlags(m).userInvalidated=true;}
return m;}
var momentProperties=utils_hooks__hooks.momentProperties=[];function copyConfig(to,from){var i,prop,val;if(typeof from._isAMomentObject!=='undefined'){to._isAMomentObject=from._isAMomentObject;}
if(typeof from._i!=='undefined'){to._i=from._i;}
if(typeof from._f!=='undefined'){to._f=from._f;}
if(typeof from._l!=='undefined'){to._l=from._l;}
if(typeof from._strict!=='undefined'){to._strict=from._strict;}
if(typeof from._tzm!=='undefined'){to._tzm=from._tzm;}
if(typeof from._isUTC!=='undefined'){to._isUTC=from._isUTC;}
if(typeof from._offset!=='undefined'){to._offset=from._offset;}
if(typeof from._pf!=='undefined'){to._pf=getParsingFlags(from);}
if(typeof from._locale!=='undefined'){to._locale=from._locale;}
if(momentProperties.length>0){for(i in momentProperties){prop=momentProperties[i];val=from[prop];if(typeof val!=='undefined'){to[prop]=val;}}}
return to;}
var updateInProgress=false;function Moment(config){copyConfig(this,config);this._d=new Date(config._d!=null?config._d.getTime():NaN);if(updateInProgress===false){updateInProgress=true;utils_hooks__hooks.updateOffset(this);updateInProgress=false;}}
function isMoment(obj){return obj instanceof Moment||(obj!=null&&obj._isAMomentObject!=null);}
function absFloor(number){if(number<0){return Math.ceil(number);}else{return Math.floor(number);}}
function toInt(argumentForCoercion){var coercedNumber=+argumentForCoercion,value=0;if(coercedNumber!==0&&isFinite(coercedNumber)){value=absFloor(coercedNumber);}
return value;}
function compareArrays(array1,array2,dontConvert){var len=Math.min(array1.length,array2.length),lengthDiff=Math.abs(array1.length-array2.length),diffs=0,i;for(i=0;i<len;i++){if((dontConvert&&array1[i]!==array2[i])||(!dontConvert&&toInt(array1[i])!==toInt(array2[i]))){diffs++;}}
return diffs+lengthDiff;}
function Locale(){}
var locales={};var globalLocale;function normalizeLocale(key){return key?key.toLowerCase().replace('_','-'):key;}
function chooseLocale(names){var i=0,j,next,locale,split;while(i<names.length){split=normalizeLocale(names[i]).split('-');j=split.length;next=normalizeLocale(names[i+1]);next=next?next.split('-'):null;while(j>0){locale=loadLocale(split.slice(0,j).join('-'));if(locale){return locale;}
if(next&&next.length>=j&&compareArrays(split,next,true)>=j-1){break;}
j--;}
i++;}
return null;}
function loadLocale(name){var oldLocale=null;if(!locales[name]&&typeof module!=='undefined'&&module&&module.exports){try{oldLocale=globalLocale._abbr;require('./locale/'+name);locale_locales__getSetGlobalLocale(oldLocale);}catch(e){}}
return locales[name];}
function locale_locales__getSetGlobalLocale(key,values){var data;if(key){if(typeof values==='undefined'){data=locale_locales__getLocale(key);}
else{data=defineLocale(key,values);}
if(data){globalLocale=data;}}
return globalLocale._abbr;}
function defineLocale(name,values){if(values!==null){values.abbr=name;locales[name]=locales[name]||new Locale();locales[name].set(values);locale_locales__getSetGlobalLocale(name);return locales[name];}else{delete locales[name];return null;}}
function locale_locales__getLocale(key){var locale;if(key&&key._locale&&key._locale._abbr){key=key._locale._abbr;}
if(!key){return globalLocale;}
if(!isArray(key)){locale=loadLocale(key);if(locale){return locale;}
key=[key];}
return chooseLocale(key);}
var aliases={};function addUnitAlias(unit,shorthand){var lowerCase=unit.toLowerCase();aliases[lowerCase]=aliases[lowerCase+'s']=aliases[shorthand]=unit;}
function normalizeUnits(units){return typeof units==='string'?aliases[units]||aliases[units.toLowerCase()]:undefined;}
function normalizeObjectUnits(inputObject){var normalizedInput={},normalizedProp,prop;for(prop in inputObject){if(hasOwnProp(inputObject,prop)){normalizedProp=normalizeUnits(prop);if(normalizedProp){normalizedInput[normalizedProp]=inputObject[prop];}}}
return normalizedInput;}
function makeGetSet(unit,keepTime){return function(value){if(value!=null){get_set__set(this,unit,value);utils_hooks__hooks.updateOffset(this,keepTime);return this;}else{return get_set__get(this,unit);}};}
function get_set__get(mom,unit){return mom._d['get'+(mom._isUTC?'UTC':'')+unit]();}
function get_set__set(mom,unit,value){return mom._d['set'+(mom._isUTC?'UTC':'')+unit](value);}
function getSet(units,value){var unit;if(typeof units==='object'){for(unit in units){this.set(unit,units[unit]);}}else{units=normalizeUnits(units);if(typeof this[units]==='function'){return this[units](value);}}
return this;}
function zeroFill(number,targetLength,forceSign){var absNumber=''+Math.abs(number),zerosToFill=targetLength-absNumber.length,sign=number>=0;return(sign?(forceSign?'+':''):'-')+
Math.pow(10,Math.max(0,zerosToFill)).toString().substr(1)+absNumber;}
var formattingTokens=/(\[[^\[]*\])|(\\)?(Mo|MM?M?M?|Do|DDDo|DD?D?D?|ddd?d?|do?|w[o|w]?|W[o|W]?|Q|YYYYYY|YYYYY|YYYY|YY|gg(ggg?)?|GG(GGG?)?|e|E|a|A|hh?|HH?|mm?|ss?|S{1,9}|x|X|zz?|ZZ?|.)/g;var localFormattingTokens=/(\[[^\[]*\])|(\\)?(LTS|LT|LL?L?L?|l{1,4})/g;var formatFunctions={};var formatTokenFunctions={};function addFormatToken(token,padded,ordinal,callback){var func=callback;if(typeof callback==='string'){func=function(){return this[callback]();};}
if(token){formatTokenFunctions[token]=func;}
if(padded){formatTokenFunctions[padded[0]]=function(){return zeroFill(func.apply(this,arguments),padded[1],padded[2]);};}
if(ordinal){formatTokenFunctions[ordinal]=function(){return this.localeData().ordinal(func.apply(this,arguments),token);};}}
function removeFormattingTokens(input){if(input.match(/\[[\s\S]/)){return input.replace(/^\[|\]$/g,'');}
return input.replace(/\\/g,'');}
function makeFormatFunction(format){var array=format.match(formattingTokens),i,length;for(i=0,length=array.length;i<length;i++){if(formatTokenFunctions[array[i]]){array[i]=formatTokenFunctions[array[i]];}else{array[i]=removeFormattingTokens(array[i]);}}
return function(mom){var output='';for(i=0;i<length;i++){output+=array[i]instanceof Function?array[i].call(mom,format):array[i];}
return output;};}
function formatMoment(m,format){if(!m.isValid()){return m.localeData().invalidDate();}
format=expandFormat(format,m.localeData());formatFunctions[format]=formatFunctions[format]||makeFormatFunction(format);return formatFunctions[format](m);}
function expandFormat(format,locale){var i=5;function replaceLongDateFormatTokens(input){return locale.longDateFormat(input)||input;}
localFormattingTokens.lastIndex=0;while(i>=0&&localFormattingTokens.test(format)){format=format.replace(localFormattingTokens,replaceLongDateFormatTokens);localFormattingTokens.lastIndex=0;i-=1;}
return format;}
var match1=/\d/;var match2=/\d\d/;var match3=/\d{3}/;var match4=/\d{4}/;var match6=/[+-]?\d{6}/;var match1to2=/\d\d?/;var match1to3=/\d{1,3}/;var match1to4=/\d{1,4}/;var match1to6=/[+-]?\d{1,6}/;var matchUnsigned=/\d+/;var matchSigned=/[+-]?\d+/;var matchOffset=/Z|[+-]\d\d:?\d\d/gi;var matchTimestamp=/[+-]?\d+(\.\d{1,3})?/;var matchWord=/[0-9]*['a-z\u00A0-\u05FF\u0700-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]+|[\u0600-\u06FF\/]+(\s*?[\u0600-\u06FF]+){1,2}/i;var regexes={};function isFunction(sth){return typeof sth==='function'&&Object.prototype.toString.call(sth)==='[object Function]';}
function addRegexToken(token,regex,strictRegex){regexes[token]=isFunction(regex)?regex:function(isStrict){return(isStrict&&strictRegex)?strictRegex:regex;};}
function getParseRegexForToken(token,config){if(!hasOwnProp(regexes,token)){return new RegExp(unescapeFormat(token));}
return regexes[token](config._strict,config._locale);}
function unescapeFormat(s){return s.replace('\\','').replace(/\\(\[)|\\(\])|\[([^\]\[]*)\]|\\(.)/g,function(matched,p1,p2,p3,p4){return p1||p2||p3||p4;}).replace(/[-\/\\^$*+?.()|[\]{}]/g,'\\$&');}
var tokens={};function addParseToken(token,callback){var i,func=callback;if(typeof token==='string'){token=[token];}
if(typeof callback==='number'){func=function(input,array){array[callback]=toInt(input);};}
for(i=0;i<token.length;i++){tokens[token[i]]=func;}}
function addWeekParseToken(token,callback){addParseToken(token,function(input,array,config,token){config._w=config._w||{};callback(input,config._w,config,token);});}
function addTimeToArrayFromToken(token,input,config){if(input!=null&&hasOwnProp(tokens,token)){tokens[token](input,config._a,config,token);}}
var YEAR=0;var MONTH=1;var DATE=2;var HOUR=3;var MINUTE=4;var SECOND=5;var MILLISECOND=6;function daysInMonth(year,month){return new Date(Date.UTC(year,month+1,0)).getUTCDate();}
addFormatToken('M',['MM',2],'Mo',function(){return this.month()+1;});addFormatToken('MMM',0,0,function(format){return this.localeData().monthsShort(this,format);});addFormatToken('MMMM',0,0,function(format){return this.localeData().months(this,format);});addUnitAlias('month','M');addRegexToken('M',match1to2);addRegexToken('MM',match1to2,match2);addRegexToken('MMM',matchWord);addRegexToken('MMMM',matchWord);addParseToken(['M','MM'],function(input,array){array[MONTH]=toInt(input)-1;});addParseToken(['MMM','MMMM'],function(input,array,config,token){var month=config._locale.monthsParse(input,token,config._strict);if(month!=null){array[MONTH]=month;}else{getParsingFlags(config).invalidMonth=input;}});var defaultLocaleMonths='January_February_March_April_May_June_July_August_September_October_November_December'.split('_');function localeMonths(m){return this._months[m.month()];}
var defaultLocaleMonthsShort='Jan_Feb_Mar_Apr_May_Jun_Jul_Aug_Sep_Oct_Nov_Dec'.split('_');function localeMonthsShort(m){return this._monthsShort[m.month()];}
function localeMonthsParse(monthName,format,strict){var i,mom,regex;if(!this._monthsParse){this._monthsParse=[];this._longMonthsParse=[];this._shortMonthsParse=[];}
for(i=0;i<12;i++){mom=create_utc__createUTC([2000,i]);if(strict&&!this._longMonthsParse[i]){this._longMonthsParse[i]=new RegExp('^'+this.months(mom,'').replace('.','')+'$','i');this._shortMonthsParse[i]=new RegExp('^'+this.monthsShort(mom,'').replace('.','')+'$','i');}
if(!strict&&!this._monthsParse[i]){regex='^'+this.months(mom,'')+'|^'+this.monthsShort(mom,'');this._monthsParse[i]=new RegExp(regex.replace('.',''),'i');}
if(strict&&format==='MMMM'&&this._longMonthsParse[i].test(monthName)){return i;}else if(strict&&format==='MMM'&&this._shortMonthsParse[i].test(monthName)){return i;}else if(!strict&&this._monthsParse[i].test(monthName)){return i;}}}
function setMonth(mom,value){var dayOfMonth;if(typeof value==='string'){value=mom.localeData().monthsParse(value);if(typeof value!=='number'){return mom;}}
dayOfMonth=Math.min(mom.date(),daysInMonth(mom.year(),value));mom._d['set'+(mom._isUTC?'UTC':'')+'Month'](value,dayOfMonth);return mom;}
function getSetMonth(value){if(value!=null){setMonth(this,value);utils_hooks__hooks.updateOffset(this,true);return this;}else{return get_set__get(this,'Month');}}
function getDaysInMonth(){return daysInMonth(this.year(),this.month());}
function checkOverflow(m){var overflow;var a=m._a;if(a&&getParsingFlags(m).overflow===-2){overflow=a[MONTH]<0||a[MONTH]>11?MONTH:a[DATE]<1||a[DATE]>daysInMonth(a[YEAR],a[MONTH])?DATE:a[HOUR]<0||a[HOUR]>24||(a[HOUR]===24&&(a[MINUTE]!==0||a[SECOND]!==0||a[MILLISECOND]!==0))?HOUR:a[MINUTE]<0||a[MINUTE]>59?MINUTE:a[SECOND]<0||a[SECOND]>59?SECOND:a[MILLISECOND]<0||a[MILLISECOND]>999?MILLISECOND:-1;if(getParsingFlags(m)._overflowDayOfYear&&(overflow<YEAR||overflow>DATE)){overflow=DATE;}
getParsingFlags(m).overflow=overflow;}
return m;}
function warn(msg){if(utils_hooks__hooks.suppressDeprecationWarnings===false&&typeof console!=='undefined'&&console.warn){console.warn('Deprecation warning: '+msg);}}
function deprecate(msg,fn){var firstTime=true;return extend(function(){if(firstTime){warn(msg+'\n'+(new Error()).stack);firstTime=false;}
return fn.apply(this,arguments);},fn);}
var deprecations={};function deprecateSimple(name,msg){if(!deprecations[name]){warn(msg);deprecations[name]=true;}}
utils_hooks__hooks.suppressDeprecationWarnings=false;var from_string__isoRegex=/^\s*(?:[+-]\d{6}|\d{4})-(?:(\d\d-\d\d)|(W\d\d$)|(W\d\d-\d)|(\d\d\d))((T| )(\d\d(:\d\d(:\d\d(\.\d+)?)?)?)?([\+\-]\d\d(?::?\d\d)?|\s*Z)?)?$/;var isoDates=[['YYYYYY-MM-DD',/[+-]\d{6}-\d{2}-\d{2}/],['YYYY-MM-DD',/\d{4}-\d{2}-\d{2}/],['GGGG-[W]WW-E',/\d{4}-W\d{2}-\d/],['GGGG-[W]WW',/\d{4}-W\d{2}/],['YYYY-DDD',/\d{4}-\d{3}/]];var isoTimes=[['HH:mm:ss.SSSS',/(T| )\d\d:\d\d:\d\d\.\d+/],['HH:mm:ss',/(T| )\d\d:\d\d:\d\d/],['HH:mm',/(T| )\d\d:\d\d/],['HH',/(T| )\d\d/]];var aspNetJsonRegex=/^\/?Date\((\-?\d+)/i;function configFromISO(config){var i,l,string=config._i,match=from_string__isoRegex.exec(string);if(match){getParsingFlags(config).iso=true;for(i=0,l=isoDates.length;i<l;i++){if(isoDates[i][1].exec(string)){config._f=isoDates[i][0];break;}}
for(i=0,l=isoTimes.length;i<l;i++){if(isoTimes[i][1].exec(string)){config._f+=(match[6]||' ')+isoTimes[i][0];break;}}
if(string.match(matchOffset)){config._f+='Z';}
configFromStringAndFormat(config);}else{config._isValid=false;}}
function configFromString(config){var matched=aspNetJsonRegex.exec(config._i);if(matched!==null){config._d=new Date(+matched[1]);return;}
configFromISO(config);if(config._isValid===false){delete config._isValid;utils_hooks__hooks.createFromInputFallback(config);}}
utils_hooks__hooks.createFromInputFallback=deprecate('moment construction falls back to js Date. This is '+'discouraged and will be removed in upcoming major '+'release. Please refer to '+'https://github.com/moment/moment/issues/1407 for more info.',function(config){config._d=new Date(config._i+(config._useUTC?' UTC':''));});function createDate(y,m,d,h,M,s,ms){var date=new Date(y,m,d,h,M,s,ms);if(y<1970){date.setFullYear(y);}
return date;}
function createUTCDate(y){var date=new Date(Date.UTC.apply(null,arguments));if(y<1970){date.setUTCFullYear(y);}
return date;}
addFormatToken(0,['YY',2],0,function(){return this.year()%100;});addFormatToken(0,['YYYY',4],0,'year');addFormatToken(0,['YYYYY',5],0,'year');addFormatToken(0,['YYYYYY',6,true],0,'year');addUnitAlias('year','y');addRegexToken('Y',matchSigned);addRegexToken('YY',match1to2,match2);addRegexToken('YYYY',match1to4,match4);addRegexToken('YYYYY',match1to6,match6);addRegexToken('YYYYYY',match1to6,match6);addParseToken(['YYYYY','YYYYYY'],YEAR);addParseToken('YYYY',function(input,array){array[YEAR]=input.length===2?utils_hooks__hooks.parseTwoDigitYear(input):toInt(input);});addParseToken('YY',function(input,array){array[YEAR]=utils_hooks__hooks.parseTwoDigitYear(input);});function daysInYear(year){return isLeapYear(year)?366:365;}
function isLeapYear(year){return(year%4===0&&year%100!==0)||year%400===0;}
utils_hooks__hooks.parseTwoDigitYear=function(input){return toInt(input)+(toInt(input)>68?1900:2000);};var getSetYear=makeGetSet('FullYear',false);function getIsLeapYear(){return isLeapYear(this.year());}
addFormatToken('w',['ww',2],'wo','week');addFormatToken('W',['WW',2],'Wo','isoWeek');addUnitAlias('week','w');addUnitAlias('isoWeek','W');addRegexToken('w',match1to2);addRegexToken('ww',match1to2,match2);addRegexToken('W',match1to2);addRegexToken('WW',match1to2,match2);addWeekParseToken(['w','ww','W','WW'],function(input,week,config,token){week[token.substr(0,1)]=toInt(input);});function weekOfYear(mom,firstDayOfWeek,firstDayOfWeekOfYear){var end=firstDayOfWeekOfYear-firstDayOfWeek,daysToDayOfWeek=firstDayOfWeekOfYear-mom.day(),adjustedMoment;if(daysToDayOfWeek>end){daysToDayOfWeek-=7;}
if(daysToDayOfWeek<end-7){daysToDayOfWeek+=7;}
adjustedMoment=local__createLocal(mom).add(daysToDayOfWeek,'d');return{week:Math.ceil(adjustedMoment.dayOfYear()/7),year:adjustedMoment.year()};}
function localeWeek(mom){return weekOfYear(mom,this._week.dow,this._week.doy).week;}
var defaultLocaleWeek={dow:0,doy:6};function localeFirstDayOfWeek(){return this._week.dow;}
function localeFirstDayOfYear(){return this._week.doy;}
function getSetWeek(input){var week=this.localeData().week(this);return input==null?week:this.add((input-week)*7,'d');}
function getSetISOWeek(input){var week=weekOfYear(this,1,4).week;return input==null?week:this.add((input-week)*7,'d');}
addFormatToken('DDD',['DDDD',3],'DDDo','dayOfYear');addUnitAlias('dayOfYear','DDD');addRegexToken('DDD',match1to3);addRegexToken('DDDD',match3);addParseToken(['DDD','DDDD'],function(input,array,config){config._dayOfYear=toInt(input);});function dayOfYearFromWeeks(year,week,weekday,firstDayOfWeekOfYear,firstDayOfWeek){var week1Jan=6+firstDayOfWeek-firstDayOfWeekOfYear,janX=createUTCDate(year,0,1+week1Jan),d=janX.getUTCDay(),dayOfYear;if(d<firstDayOfWeek){d+=7;}
weekday=weekday!=null?1*weekday:firstDayOfWeek;dayOfYear=1+week1Jan+7*(week-1)-d+weekday;return{year:dayOfYear>0?year:year-1,dayOfYear:dayOfYear>0?dayOfYear:daysInYear(year-1)+dayOfYear};}
function getSetDayOfYear(input){var dayOfYear=Math.round((this.clone().startOf('day')-this.clone().startOf('year'))/864e5)+1;return input==null?dayOfYear:this.add((input-dayOfYear),'d');}
function defaults(a,b,c){if(a!=null){return a;}
if(b!=null){return b;}
return c;}
function currentDateArray(config){var now=new Date();if(config._useUTC){return[now.getUTCFullYear(),now.getUTCMonth(),now.getUTCDate()];}
return[now.getFullYear(),now.getMonth(),now.getDate()];}
function configFromArray(config){var i,date,input=[],currentDate,yearToUse;if(config._d){return;}
currentDate=currentDateArray(config);if(config._w&&config._a[DATE]==null&&config._a[MONTH]==null){dayOfYearFromWeekInfo(config);}
if(config._dayOfYear){yearToUse=defaults(config._a[YEAR],currentDate[YEAR]);if(config._dayOfYear>daysInYear(yearToUse)){getParsingFlags(config)._overflowDayOfYear=true;}
date=createUTCDate(yearToUse,0,config._dayOfYear);config._a[MONTH]=date.getUTCMonth();config._a[DATE]=date.getUTCDate();}
for(i=0;i<3&&config._a[i]==null;++i){config._a[i]=input[i]=currentDate[i];}
for(;i<7;i++){config._a[i]=input[i]=(config._a[i]==null)?(i===2?1:0):config._a[i];}
if(config._a[HOUR]===24&&config._a[MINUTE]===0&&config._a[SECOND]===0&&config._a[MILLISECOND]===0){config._nextDay=true;config._a[HOUR]=0;}
config._d=(config._useUTC?createUTCDate:createDate).apply(null,input);if(config._tzm!=null){config._d.setUTCMinutes(config._d.getUTCMinutes()-config._tzm);}
if(config._nextDay){config._a[HOUR]=24;}}
function dayOfYearFromWeekInfo(config){var w,weekYear,week,weekday,dow,doy,temp;w=config._w;if(w.GG!=null||w.W!=null||w.E!=null){dow=1;doy=4;weekYear=defaults(w.GG,config._a[YEAR],weekOfYear(local__createLocal(),1,4).year);week=defaults(w.W,1);weekday=defaults(w.E,1);}else{dow=config._locale._week.dow;doy=config._locale._week.doy;weekYear=defaults(w.gg,config._a[YEAR],weekOfYear(local__createLocal(),dow,doy).year);week=defaults(w.w,1);if(w.d!=null){weekday=w.d;if(weekday<dow){++week;}}else if(w.e!=null){weekday=w.e+dow;}else{weekday=dow;}}
temp=dayOfYearFromWeeks(weekYear,week,weekday,doy,dow);config._a[YEAR]=temp.year;config._dayOfYear=temp.dayOfYear;}
utils_hooks__hooks.ISO_8601=function(){};function configFromStringAndFormat(config){if(config._f===utils_hooks__hooks.ISO_8601){configFromISO(config);return;}
config._a=[];getParsingFlags(config).empty=true;var string=''+config._i,i,parsedInput,tokens,token,skipped,stringLength=string.length,totalParsedInputLength=0;tokens=expandFormat(config._f,config._locale).match(formattingTokens)||[];for(i=0;i<tokens.length;i++){token=tokens[i];parsedInput=(string.match(getParseRegexForToken(token,config))||[])[0];if(parsedInput){skipped=string.substr(0,string.indexOf(parsedInput));if(skipped.length>0){getParsingFlags(config).unusedInput.push(skipped);}
string=string.slice(string.indexOf(parsedInput)+parsedInput.length);totalParsedInputLength+=parsedInput.length;}
if(formatTokenFunctions[token]){if(parsedInput){getParsingFlags(config).empty=false;}
else{getParsingFlags(config).unusedTokens.push(token);}
addTimeToArrayFromToken(token,parsedInput,config);}
else if(config._strict&&!parsedInput){getParsingFlags(config).unusedTokens.push(token);}}
getParsingFlags(config).charsLeftOver=stringLength-totalParsedInputLength;if(string.length>0){getParsingFlags(config).unusedInput.push(string);}
if(getParsingFlags(config).bigHour===true&&config._a[HOUR]<=12&&config._a[HOUR]>0){getParsingFlags(config).bigHour=undefined;}
config._a[HOUR]=meridiemFixWrap(config._locale,config._a[HOUR],config._meridiem);configFromArray(config);checkOverflow(config);}
function meridiemFixWrap(locale,hour,meridiem){var isPm;if(meridiem==null){return hour;}
if(locale.meridiemHour!=null){return locale.meridiemHour(hour,meridiem);}else if(locale.isPM!=null){isPm=locale.isPM(meridiem);if(isPm&&hour<12){hour+=12;}
if(!isPm&&hour===12){hour=0;}
return hour;}else{return hour;}}
function configFromStringAndArray(config){var tempConfig,bestMoment,scoreToBeat,i,currentScore;if(config._f.length===0){getParsingFlags(config).invalidFormat=true;config._d=new Date(NaN);return;}
for(i=0;i<config._f.length;i++){currentScore=0;tempConfig=copyConfig({},config);if(config._useUTC!=null){tempConfig._useUTC=config._useUTC;}
tempConfig._f=config._f[i];configFromStringAndFormat(tempConfig);if(!valid__isValid(tempConfig)){continue;}
currentScore+=getParsingFlags(tempConfig).charsLeftOver;currentScore+=getParsingFlags(tempConfig).unusedTokens.length*10;getParsingFlags(tempConfig).score=currentScore;if(scoreToBeat==null||currentScore<scoreToBeat){scoreToBeat=currentScore;bestMoment=tempConfig;}}
extend(config,bestMoment||tempConfig);}
function configFromObject(config){if(config._d){return;}
var i=normalizeObjectUnits(config._i);config._a=[i.year,i.month,i.day||i.date,i.hour,i.minute,i.second,i.millisecond];configFromArray(config);}
function createFromConfig(config){var res=new Moment(checkOverflow(prepareConfig(config)));if(res._nextDay){res.add(1,'d');res._nextDay=undefined;}
return res;}
function prepareConfig(config){var input=config._i,format=config._f;config._locale=config._locale||locale_locales__getLocale(config._l);if(input===null||(format===undefined&&input==='')){return valid__createInvalid({nullInput:true});}
if(typeof input==='string'){config._i=input=config._locale.preparse(input);}
if(isMoment(input)){return new Moment(checkOverflow(input));}else if(isArray(format)){configFromStringAndArray(config);}else if(format){configFromStringAndFormat(config);}else if(isDate(input)){config._d=input;}else{configFromInput(config);}
return config;}
function configFromInput(config){var input=config._i;if(input===undefined){config._d=new Date();}else if(isDate(input)){config._d=new Date(+input);}else if(typeof input==='string'){configFromString(config);}else if(isArray(input)){config._a=map(input.slice(0),function(obj){return parseInt(obj,10);});configFromArray(config);}else if(typeof(input)==='object'){configFromObject(config);}else if(typeof(input)==='number'){config._d=new Date(input);}else{utils_hooks__hooks.createFromInputFallback(config);}}
function createLocalOrUTC(input,format,locale,strict,isUTC){var c={};if(typeof(locale)==='boolean'){strict=locale;locale=undefined;}
c._isAMomentObject=true;c._useUTC=c._isUTC=isUTC;c._l=locale;c._i=input;c._f=format;c._strict=strict;return createFromConfig(c);}
function local__createLocal(input,format,locale,strict){return createLocalOrUTC(input,format,locale,strict,false);}
var prototypeMin=deprecate('moment().min is deprecated, use moment.min instead. https://github.com/moment/moment/issues/1548',function(){var other=local__createLocal.apply(null,arguments);return other<this?this:other;});var prototypeMax=deprecate('moment().max is deprecated, use moment.max instead. https://github.com/moment/moment/issues/1548',function(){var other=local__createLocal.apply(null,arguments);return other>this?this:other;});function pickBy(fn,moments){var res,i;if(moments.length===1&&isArray(moments[0])){moments=moments[0];}
if(!moments.length){return local__createLocal();}
res=moments[0];for(i=1;i<moments.length;++i){if(!moments[i].isValid()||moments[i][fn](res)){res=moments[i];}}
return res;}
function min(){var args=[].slice.call(arguments,0);return pickBy('isBefore',args);}
function max(){var args=[].slice.call(arguments,0);return pickBy('isAfter',args);}
function Duration(duration){var normalizedInput=normalizeObjectUnits(duration),years=normalizedInput.year||0,quarters=normalizedInput.quarter||0,months=normalizedInput.month||0,weeks=normalizedInput.week||0,days=normalizedInput.day||0,hours=normalizedInput.hour||0,minutes=normalizedInput.minute||0,seconds=normalizedInput.second||0,milliseconds=normalizedInput.millisecond||0;this._milliseconds=+milliseconds+
seconds*1e3+
minutes*6e4+
hours*36e5;this._days=+days+
weeks*7;this._months=+months+
quarters*3+
years*12;this._data={};this._locale=locale_locales__getLocale();this._bubble();}
function isDuration(obj){return obj instanceof Duration;}
function offset(token,separator){addFormatToken(token,0,0,function(){var offset=this.utcOffset();var sign='+';if(offset<0){offset=-offset;sign='-';}
return sign+zeroFill(~~(offset/60),2)+separator+zeroFill(~~(offset)%60,2);});}
offset('Z',':');offset('ZZ','');addRegexToken('Z',matchOffset);addRegexToken('ZZ',matchOffset);addParseToken(['Z','ZZ'],function(input,array,config){config._useUTC=true;config._tzm=offsetFromString(input);});var chunkOffset=/([\+\-]|\d\d)/gi;function offsetFromString(string){var matches=((string||'').match(matchOffset)||[]);var chunk=matches[matches.length-1]||[];var parts=(chunk+'').match(chunkOffset)||['-',0,0];var minutes=+(parts[1]*60)+toInt(parts[2]);return parts[0]==='+'?minutes:-minutes;}
function cloneWithOffset(input,model){var res,diff;if(model._isUTC){res=model.clone();diff=(isMoment(input)||isDate(input)?+input:+local__createLocal(input))-(+res);res._d.setTime(+res._d+diff);utils_hooks__hooks.updateOffset(res,false);return res;}else{return local__createLocal(input).local();}}
function getDateOffset(m){return-Math.round(m._d.getTimezoneOffset()/15)*15;}
utils_hooks__hooks.updateOffset=function(){};function getSetOffset(input,keepLocalTime){var offset=this._offset||0,localAdjust;if(input!=null){if(typeof input==='string'){input=offsetFromString(input);}
if(Math.abs(input)<16){input=input*60;}
if(!this._isUTC&&keepLocalTime){localAdjust=getDateOffset(this);}
this._offset=input;this._isUTC=true;if(localAdjust!=null){this.add(localAdjust,'m');}
if(offset!==input){if(!keepLocalTime||this._changeInProgress){add_subtract__addSubtract(this,create__createDuration(input-offset,'m'),1,false);}else if(!this._changeInProgress){this._changeInProgress=true;utils_hooks__hooks.updateOffset(this,true);this._changeInProgress=null;}}
return this;}else{return this._isUTC?offset:getDateOffset(this);}}
function getSetZone(input,keepLocalTime){if(input!=null){if(typeof input!=='string'){input=-input;}
this.utcOffset(input,keepLocalTime);return this;}else{return-this.utcOffset();}}
function setOffsetToUTC(keepLocalTime){return this.utcOffset(0,keepLocalTime);}
function setOffsetToLocal(keepLocalTime){if(this._isUTC){this.utcOffset(0,keepLocalTime);this._isUTC=false;if(keepLocalTime){this.subtract(getDateOffset(this),'m');}}
return this;}
function setOffsetToParsedOffset(){if(this._tzm){this.utcOffset(this._tzm);}else if(typeof this._i==='string'){this.utcOffset(offsetFromString(this._i));}
return this;}
function hasAlignedHourOffset(input){input=input?local__createLocal(input).utcOffset():0;return(this.utcOffset()-input)%60===0;}
function isDaylightSavingTime(){return(this.utcOffset()>this.clone().month(0).utcOffset()||this.utcOffset()>this.clone().month(5).utcOffset());}
function isDaylightSavingTimeShifted(){if(typeof this._isDSTShifted!=='undefined'){return this._isDSTShifted;}
var c={};copyConfig(c,this);c=prepareConfig(c);if(c._a){var other=c._isUTC?create_utc__createUTC(c._a):local__createLocal(c._a);this._isDSTShifted=this.isValid()&&compareArrays(c._a,other.toArray())>0;}else{this._isDSTShifted=false;}
return this._isDSTShifted;}
function isLocal(){return!this._isUTC;}
function isUtcOffset(){return this._isUTC;}
function isUtc(){return this._isUTC&&this._offset===0;}
var aspNetRegex=/(\-)?(?:(\d*)\.)?(\d+)\:(\d+)(?:\:(\d+)\.?(\d{3})?)?/;var create__isoRegex=/^(-)?P(?:(?:([0-9,.]*)Y)?(?:([0-9,.]*)M)?(?:([0-9,.]*)D)?(?:T(?:([0-9,.]*)H)?(?:([0-9,.]*)M)?(?:([0-9,.]*)S)?)?|([0-9,.]*)W)$/;function create__createDuration(input,key){var duration=input,match=null,sign,ret,diffRes;if(isDuration(input)){duration={ms:input._milliseconds,d:input._days,M:input._months};}else if(typeof input==='number'){duration={};if(key){duration[key]=input;}else{duration.milliseconds=input;}}else if(!!(match=aspNetRegex.exec(input))){sign=(match[1]==='-')?-1:1;duration={y:0,d:toInt(match[DATE])*sign,h:toInt(match[HOUR])*sign,m:toInt(match[MINUTE])*sign,s:toInt(match[SECOND])*sign,ms:toInt(match[MILLISECOND])*sign};}else if(!!(match=create__isoRegex.exec(input))){sign=(match[1]==='-')?-1:1;duration={y:parseIso(match[2],sign),M:parseIso(match[3],sign),d:parseIso(match[4],sign),h:parseIso(match[5],sign),m:parseIso(match[6],sign),s:parseIso(match[7],sign),w:parseIso(match[8],sign)};}else if(duration==null){duration={};}else if(typeof duration==='object'&&('from'in duration||'to'in duration)){diffRes=momentsDifference(local__createLocal(duration.from),local__createLocal(duration.to));duration={};duration.ms=diffRes.milliseconds;duration.M=diffRes.months;}
ret=new Duration(duration);if(isDuration(input)&&hasOwnProp(input,'_locale')){ret._locale=input._locale;}
return ret;}
create__createDuration.fn=Duration.prototype;function parseIso(inp,sign){var res=inp&&parseFloat(inp.replace(',','.'));return(isNaN(res)?0:res)*sign;}
function positiveMomentsDifference(base,other){var res={milliseconds:0,months:0};res.months=other.month()-base.month()+
(other.year()-base.year())*12;if(base.clone().add(res.months,'M').isAfter(other)){--res.months;}
res.milliseconds=+other-+(base.clone().add(res.months,'M'));return res;}
function momentsDifference(base,other){var res;other=cloneWithOffset(other,base);if(base.isBefore(other)){res=positiveMomentsDifference(base,other);}else{res=positiveMomentsDifference(other,base);res.milliseconds=-res.milliseconds;res.months=-res.months;}
return res;}
function createAdder(direction,name){return function(val,period){var dur,tmp;if(period!==null&&!isNaN(+period)){deprecateSimple(name,'moment().'+name+'(period, number) is deprecated. Please use moment().'+name+'(number, period).');tmp=val;val=period;period=tmp;}
val=typeof val==='string'?+val:val;dur=create__createDuration(val,period);add_subtract__addSubtract(this,dur,direction);return this;};}
function add_subtract__addSubtract(mom,duration,isAdding,updateOffset){var milliseconds=duration._milliseconds,days=duration._days,months=duration._months;updateOffset=updateOffset==null?true:updateOffset;if(milliseconds){mom._d.setTime(+mom._d+milliseconds*isAdding);}
if(days){get_set__set(mom,'Date',get_set__get(mom,'Date')+days*isAdding);}
if(months){setMonth(mom,get_set__get(mom,'Month')+months*isAdding);}
if(updateOffset){utils_hooks__hooks.updateOffset(mom,days||months);}}
var add_subtract__add=createAdder(1,'add');var add_subtract__subtract=createAdder(-1,'subtract');function moment_calendar__calendar(time,formats){var now=time||local__createLocal(),sod=cloneWithOffset(now,this).startOf('day'),diff=this.diff(sod,'days',true),format=diff<-6?'sameElse':diff<-1?'lastWeek':diff<0?'lastDay':diff<1?'sameDay':diff<2?'nextDay':diff<7?'nextWeek':'sameElse';return this.format(formats&&formats[format]||this.localeData().calendar(format,this,local__createLocal(now)));}
function clone(){return new Moment(this);}
function isAfter(input,units){var inputMs;units=normalizeUnits(typeof units!=='undefined'?units:'millisecond');if(units==='millisecond'){input=isMoment(input)?input:local__createLocal(input);return+this>+input;}else{inputMs=isMoment(input)?+input:+local__createLocal(input);return inputMs<+this.clone().startOf(units);}}
function isBefore(input,units){var inputMs;units=normalizeUnits(typeof units!=='undefined'?units:'millisecond');if(units==='millisecond'){input=isMoment(input)?input:local__createLocal(input);return+this<+input;}else{inputMs=isMoment(input)?+input:+local__createLocal(input);return+this.clone().endOf(units)<inputMs;}}
function isBetween(from,to,units){return this.isAfter(from,units)&&this.isBefore(to,units);}
function isSame(input,units){var inputMs;units=normalizeUnits(units||'millisecond');if(units==='millisecond'){input=isMoment(input)?input:local__createLocal(input);return+this===+input;}else{inputMs=+local__createLocal(input);return+(this.clone().startOf(units))<=inputMs&&inputMs<=+(this.clone().endOf(units));}}
function diff(input,units,asFloat){var that=cloneWithOffset(input,this),zoneDelta=(that.utcOffset()-this.utcOffset())*6e4,delta,output;units=normalizeUnits(units);if(units==='year'||units==='month'||units==='quarter'){output=monthDiff(this,that);if(units==='quarter'){output=output/3;}else if(units==='year'){output=output/12;}}else{delta=this-that;output=units==='second'?delta/1e3:units==='minute'?delta/6e4:units==='hour'?delta/36e5:units==='day'?(delta-zoneDelta)/864e5:units==='week'?(delta-zoneDelta)/6048e5:delta;}
return asFloat?output:absFloor(output);}
function monthDiff(a,b){var wholeMonthDiff=((b.year()-a.year())*12)+(b.month()-a.month()),anchor=a.clone().add(wholeMonthDiff,'months'),anchor2,adjust;if(b-anchor<0){anchor2=a.clone().add(wholeMonthDiff-1,'months');adjust=(b-anchor)/(anchor-anchor2);}else{anchor2=a.clone().add(wholeMonthDiff+1,'months');adjust=(b-anchor)/(anchor2-anchor);}
return-(wholeMonthDiff+adjust);}
utils_hooks__hooks.defaultFormat='YYYY-MM-DDTHH:mm:ssZ';function toString(){return this.clone().locale('en').format('ddd MMM DD YYYY HH:mm:ss [GMT]ZZ');}
function moment_format__toISOString(){var m=this.clone().utc();if(0<m.year()&&m.year()<=9999){if('function'===typeof Date.prototype.toISOString){return this.toDate().toISOString();}else{return formatMoment(m,'YYYY-MM-DD[T]HH:mm:ss.SSS[Z]');}}else{return formatMoment(m,'YYYYYY-MM-DD[T]HH:mm:ss.SSS[Z]');}}
function format(inputString){var output=formatMoment(this,inputString||utils_hooks__hooks.defaultFormat);return this.localeData().postformat(output);}
function from(time,withoutSuffix){if(!this.isValid()){return this.localeData().invalidDate();}
return create__createDuration({to:this,from:time}).locale(this.locale()).humanize(!withoutSuffix);}
function fromNow(withoutSuffix){return this.from(local__createLocal(),withoutSuffix);}
function to(time,withoutSuffix){if(!this.isValid()){return this.localeData().invalidDate();}
return create__createDuration({from:this,to:time}).locale(this.locale()).humanize(!withoutSuffix);}
function toNow(withoutSuffix){return this.to(local__createLocal(),withoutSuffix);}
function locale(key){var newLocaleData;if(key===undefined){return this._locale._abbr;}else{newLocaleData=locale_locales__getLocale(key);if(newLocaleData!=null){this._locale=newLocaleData;}
return this;}}
var lang=deprecate('moment().lang() is deprecated. Instead, use moment().localeData() to get the language configuration. Use moment().locale() to change languages.',function(key){if(key===undefined){return this.localeData();}else{return this.locale(key);}});function localeData(){return this._locale;}
function startOf(units){units=normalizeUnits(units);switch(units){case'year':this.month(0);case'quarter':case'month':this.date(1);case'week':case'isoWeek':case'day':this.hours(0);case'hour':this.minutes(0);case'minute':this.seconds(0);case'second':this.milliseconds(0);}
if(units==='week'){this.weekday(0);}
if(units==='isoWeek'){this.isoWeekday(1);}
if(units==='quarter'){this.month(Math.floor(this.month()/3)*3);}
return this;}
function endOf(units){units=normalizeUnits(units);if(units===undefined||units==='millisecond'){return this;}
return this.startOf(units).add(1,(units==='isoWeek'?'week':units)).subtract(1,'ms');}
function to_type__valueOf(){return+this._d-((this._offset||0)*60000);}
function unix(){return Math.floor(+this/1000);}
function toDate(){return this._offset?new Date(+this):this._d;}
function toArray(){var m=this;return[m.year(),m.month(),m.date(),m.hour(),m.minute(),m.second(),m.millisecond()];}
function toObject(){var m=this;return{years:m.year(),months:m.month(),date:m.date(),hours:m.hours(),minutes:m.minutes(),seconds:m.seconds(),milliseconds:m.milliseconds()};}
function moment_valid__isValid(){return valid__isValid(this);}
function parsingFlags(){return extend({},getParsingFlags(this));}
function invalidAt(){return getParsingFlags(this).overflow;}
addFormatToken(0,['gg',2],0,function(){return this.weekYear()%100;});addFormatToken(0,['GG',2],0,function(){return this.isoWeekYear()%100;});function addWeekYearFormatToken(token,getter){addFormatToken(0,[token,token.length],0,getter);}
addWeekYearFormatToken('gggg','weekYear');addWeekYearFormatToken('ggggg','weekYear');addWeekYearFormatToken('GGGG','isoWeekYear');addWeekYearFormatToken('GGGGG','isoWeekYear');addUnitAlias('weekYear','gg');addUnitAlias('isoWeekYear','GG');addRegexToken('G',matchSigned);addRegexToken('g',matchSigned);addRegexToken('GG',match1to2,match2);addRegexToken('gg',match1to2,match2);addRegexToken('GGGG',match1to4,match4);addRegexToken('gggg',match1to4,match4);addRegexToken('GGGGG',match1to6,match6);addRegexToken('ggggg',match1to6,match6);addWeekParseToken(['gggg','ggggg','GGGG','GGGGG'],function(input,week,config,token){week[token.substr(0,2)]=toInt(input);});addWeekParseToken(['gg','GG'],function(input,week,config,token){week[token]=utils_hooks__hooks.parseTwoDigitYear(input);});function weeksInYear(year,dow,doy){return weekOfYear(local__createLocal([year,11,31+dow-doy]),dow,doy).week;}
function getSetWeekYear(input){var year=weekOfYear(this,this.localeData()._week.dow,this.localeData()._week.doy).year;return input==null?year:this.add((input-year),'y');}
function getSetISOWeekYear(input){var year=weekOfYear(this,1,4).year;return input==null?year:this.add((input-year),'y');}
function getISOWeeksInYear(){return weeksInYear(this.year(),1,4);}
function getWeeksInYear(){var weekInfo=this.localeData()._week;return weeksInYear(this.year(),weekInfo.dow,weekInfo.doy);}
addFormatToken('Q',0,0,'quarter');addUnitAlias('quarter','Q');addRegexToken('Q',match1);addParseToken('Q',function(input,array){array[MONTH]=(toInt(input)-1)*3;});function getSetQuarter(input){return input==null?Math.ceil((this.month()+1)/3):this.month((input-1)*3+this.month()%3);}
addFormatToken('D',['DD',2],'Do','date');addUnitAlias('date','D');addRegexToken('D',match1to2);addRegexToken('DD',match1to2,match2);addRegexToken('Do',function(isStrict,locale){return isStrict?locale._ordinalParse:locale._ordinalParseLenient;});addParseToken(['D','DD'],DATE);addParseToken('Do',function(input,array){array[DATE]=toInt(input.match(match1to2)[0],10);});var getSetDayOfMonth=makeGetSet('Date',true);addFormatToken('d',0,'do','day');addFormatToken('dd',0,0,function(format){return this.localeData().weekdaysMin(this,format);});addFormatToken('ddd',0,0,function(format){return this.localeData().weekdaysShort(this,format);});addFormatToken('dddd',0,0,function(format){return this.localeData().weekdays(this,format);});addFormatToken('e',0,0,'weekday');addFormatToken('E',0,0,'isoWeekday');addUnitAlias('day','d');addUnitAlias('weekday','e');addUnitAlias('isoWeekday','E');addRegexToken('d',match1to2);addRegexToken('e',match1to2);addRegexToken('E',match1to2);addRegexToken('dd',matchWord);addRegexToken('ddd',matchWord);addRegexToken('dddd',matchWord);addWeekParseToken(['dd','ddd','dddd'],function(input,week,config){var weekday=config._locale.weekdaysParse(input);if(weekday!=null){week.d=weekday;}else{getParsingFlags(config).invalidWeekday=input;}});addWeekParseToken(['d','e','E'],function(input,week,config,token){week[token]=toInt(input);});function parseWeekday(input,locale){if(typeof input!=='string'){return input;}
if(!isNaN(input)){return parseInt(input,10);}
input=locale.weekdaysParse(input);if(typeof input==='number'){return input;}
return null;}
var defaultLocaleWeekdays='Sunday_Monday_Tuesday_Wednesday_Thursday_Friday_Saturday'.split('_');function localeWeekdays(m){return this._weekdays[m.day()];}
var defaultLocaleWeekdaysShort='Sun_Mon_Tue_Wed_Thu_Fri_Sat'.split('_');function localeWeekdaysShort(m){return this._weekdaysShort[m.day()];}
var defaultLocaleWeekdaysMin='Su_Mo_Tu_We_Th_Fr_Sa'.split('_');function localeWeekdaysMin(m){return this._weekdaysMin[m.day()];}
function localeWeekdaysParse(weekdayName){var i,mom,regex;this._weekdaysParse=this._weekdaysParse||[];for(i=0;i<7;i++){if(!this._weekdaysParse[i]){mom=local__createLocal([2000,1]).day(i);regex='^'+this.weekdays(mom,'')+'|^'+this.weekdaysShort(mom,'')+'|^'+this.weekdaysMin(mom,'');this._weekdaysParse[i]=new RegExp(regex.replace('.',''),'i');}
if(this._weekdaysParse[i].test(weekdayName)){return i;}}}
function getSetDayOfWeek(input){var day=this._isUTC?this._d.getUTCDay():this._d.getDay();if(input!=null){input=parseWeekday(input,this.localeData());return this.add(input-day,'d');}else{return day;}}
function getSetLocaleDayOfWeek(input){var weekday=(this.day()+7-this.localeData()._week.dow)%7;return input==null?weekday:this.add(input-weekday,'d');}
function getSetISODayOfWeek(input){return input==null?this.day()||7:this.day(this.day()%7?input:input-7);}
addFormatToken('H',['HH',2],0,'hour');addFormatToken('h',['hh',2],0,function(){return this.hours()%12||12;});function meridiem(token,lowercase){addFormatToken(token,0,0,function(){return this.localeData().meridiem(this.hours(),this.minutes(),lowercase);});}
meridiem('a',true);meridiem('A',false);addUnitAlias('hour','h');function matchMeridiem(isStrict,locale){return locale._meridiemParse;}
addRegexToken('a',matchMeridiem);addRegexToken('A',matchMeridiem);addRegexToken('H',match1to2);addRegexToken('h',match1to2);addRegexToken('HH',match1to2,match2);addRegexToken('hh',match1to2,match2);addParseToken(['H','HH'],HOUR);addParseToken(['a','A'],function(input,array,config){config._isPm=config._locale.isPM(input);config._meridiem=input;});addParseToken(['h','hh'],function(input,array,config){array[HOUR]=toInt(input);getParsingFlags(config).bigHour=true;});function localeIsPM(input){return((input+'').toLowerCase().charAt(0)==='p');}
var defaultLocaleMeridiemParse=/[ap]\.?m?\.?/i;function localeMeridiem(hours,minutes,isLower){if(hours>11){return isLower?'pm':'PM';}else{return isLower?'am':'AM';}}
var getSetHour=makeGetSet('Hours',true);addFormatToken('m',['mm',2],0,'minute');addUnitAlias('minute','m');addRegexToken('m',match1to2);addRegexToken('mm',match1to2,match2);addParseToken(['m','mm'],MINUTE);var getSetMinute=makeGetSet('Minutes',false);addFormatToken('s',['ss',2],0,'second');addUnitAlias('second','s');addRegexToken('s',match1to2);addRegexToken('ss',match1to2,match2);addParseToken(['s','ss'],SECOND);var getSetSecond=makeGetSet('Seconds',false);addFormatToken('S',0,0,function(){return~~(this.millisecond()/100);});addFormatToken(0,['SS',2],0,function(){return~~(this.millisecond()/10);});addFormatToken(0,['SSS',3],0,'millisecond');addFormatToken(0,['SSSS',4],0,function(){return this.millisecond()*10;});addFormatToken(0,['SSSSS',5],0,function(){return this.millisecond()*100;});addFormatToken(0,['SSSSSS',6],0,function(){return this.millisecond()*1000;});addFormatToken(0,['SSSSSSS',7],0,function(){return this.millisecond()*10000;});addFormatToken(0,['SSSSSSSS',8],0,function(){return this.millisecond()*100000;});addFormatToken(0,['SSSSSSSSS',9],0,function(){return this.millisecond()*1000000;});addUnitAlias('millisecond','ms');addRegexToken('S',match1to3,match1);addRegexToken('SS',match1to3,match2);addRegexToken('SSS',match1to3,match3);var token;for(token='SSSS';token.length<=9;token+='S'){addRegexToken(token,matchUnsigned);}
function parseMs(input,array){array[MILLISECOND]=toInt(('0.'+input)*1000);}
for(token='S';token.length<=9;token+='S'){addParseToken(token,parseMs);}
var getSetMillisecond=makeGetSet('Milliseconds',false);addFormatToken('z',0,0,'zoneAbbr');addFormatToken('zz',0,0,'zoneName');function getZoneAbbr(){return this._isUTC?'UTC':'';}
function getZoneName(){return this._isUTC?'Coordinated Universal Time':'';}
var momentPrototype__proto=Moment.prototype;momentPrototype__proto.add=add_subtract__add;momentPrototype__proto.calendar=moment_calendar__calendar;momentPrototype__proto.clone=clone;momentPrototype__proto.diff=diff;momentPrototype__proto.endOf=endOf;momentPrototype__proto.format=format;momentPrototype__proto.from=from;momentPrototype__proto.fromNow=fromNow;momentPrototype__proto.to=to;momentPrototype__proto.toNow=toNow;momentPrototype__proto.get=getSet;momentPrototype__proto.invalidAt=invalidAt;momentPrototype__proto.isAfter=isAfter;momentPrototype__proto.isBefore=isBefore;momentPrototype__proto.isBetween=isBetween;momentPrototype__proto.isSame=isSame;momentPrototype__proto.isValid=moment_valid__isValid;momentPrototype__proto.lang=lang;momentPrototype__proto.locale=locale;momentPrototype__proto.localeData=localeData;momentPrototype__proto.max=prototypeMax;momentPrototype__proto.min=prototypeMin;momentPrototype__proto.parsingFlags=parsingFlags;momentPrototype__proto.set=getSet;momentPrototype__proto.startOf=startOf;momentPrototype__proto.subtract=add_subtract__subtract;momentPrototype__proto.toArray=toArray;momentPrototype__proto.toObject=toObject;momentPrototype__proto.toDate=toDate;momentPrototype__proto.toISOString=moment_format__toISOString;momentPrototype__proto.toJSON=moment_format__toISOString;momentPrototype__proto.toString=toString;momentPrototype__proto.unix=unix;momentPrototype__proto.valueOf=to_type__valueOf;momentPrototype__proto.year=getSetYear;momentPrototype__proto.isLeapYear=getIsLeapYear;momentPrototype__proto.weekYear=getSetWeekYear;momentPrototype__proto.isoWeekYear=getSetISOWeekYear;momentPrototype__proto.quarter=momentPrototype__proto.quarters=getSetQuarter;momentPrototype__proto.month=getSetMonth;momentPrototype__proto.daysInMonth=getDaysInMonth;momentPrototype__proto.week=momentPrototype__proto.weeks=getSetWeek;momentPrototype__proto.isoWeek=momentPrototype__proto.isoWeeks=getSetISOWeek;momentPrototype__proto.weeksInYear=getWeeksInYear;momentPrototype__proto.isoWeeksInYear=getISOWeeksInYear;momentPrototype__proto.date=getSetDayOfMonth;momentPrototype__proto.day=momentPrototype__proto.days=getSetDayOfWeek;momentPrototype__proto.weekday=getSetLocaleDayOfWeek;momentPrototype__proto.isoWeekday=getSetISODayOfWeek;momentPrototype__proto.dayOfYear=getSetDayOfYear;momentPrototype__proto.hour=momentPrototype__proto.hours=getSetHour;momentPrototype__proto.minute=momentPrototype__proto.minutes=getSetMinute;momentPrototype__proto.second=momentPrototype__proto.seconds=getSetSecond;momentPrototype__proto.millisecond=momentPrototype__proto.milliseconds=getSetMillisecond;momentPrototype__proto.utcOffset=getSetOffset;momentPrototype__proto.utc=setOffsetToUTC;momentPrototype__proto.local=setOffsetToLocal;momentPrototype__proto.parseZone=setOffsetToParsedOffset;momentPrototype__proto.hasAlignedHourOffset=hasAlignedHourOffset;momentPrototype__proto.isDST=isDaylightSavingTime;momentPrototype__proto.isDSTShifted=isDaylightSavingTimeShifted;momentPrototype__proto.isLocal=isLocal;momentPrototype__proto.isUtcOffset=isUtcOffset;momentPrototype__proto.isUtc=isUtc;momentPrototype__proto.isUTC=isUtc;momentPrototype__proto.zoneAbbr=getZoneAbbr;momentPrototype__proto.zoneName=getZoneName;momentPrototype__proto.dates=deprecate('dates accessor is deprecated. Use date instead.',getSetDayOfMonth);momentPrototype__proto.months=deprecate('months accessor is deprecated. Use month instead',getSetMonth);momentPrototype__proto.years=deprecate('years accessor is deprecated. Use year instead',getSetYear);momentPrototype__proto.zone=deprecate('moment().zone is deprecated, use moment().utcOffset instead. https://github.com/moment/moment/issues/1779',getSetZone);var momentPrototype=momentPrototype__proto;function moment__createUnix(input){return local__createLocal(input*1000);}
function moment__createInZone(){return local__createLocal.apply(null,arguments).parseZone();}
var defaultCalendar={sameDay:'[Today at] LT',nextDay:'[Tomorrow at] LT',nextWeek:'dddd [at] LT',lastDay:'[Yesterday at] LT',lastWeek:'[Last] dddd [at] LT',sameElse:'L'};function locale_calendar__calendar(key,mom,now){var output=this._calendar[key];return typeof output==='function'?output.call(mom,now):output;}
var defaultLongDateFormat={LTS:'h:mm:ss A',LT:'h:mm A',L:'MM/DD/YYYY',LL:'MMMM D, YYYY',LLL:'MMMM D, YYYY h:mm A',LLLL:'dddd, MMMM D, YYYY h:mm A'};function longDateFormat(key){var format=this._longDateFormat[key],formatUpper=this._longDateFormat[key.toUpperCase()];if(format||!formatUpper){return format;}
this._longDateFormat[key]=formatUpper.replace(/MMMM|MM|DD|dddd/g,function(val){return val.slice(1);});return this._longDateFormat[key];}
var defaultInvalidDate='Invalid date';function invalidDate(){return this._invalidDate;}
var defaultOrdinal='%d';var defaultOrdinalParse=/\d{1,2}/;function ordinal(number){return this._ordinal.replace('%d',number);}
function preParsePostFormat(string){return string;}
var defaultRelativeTime={future:'in %s',past:'%s ago',s:'a few seconds',m:'a minute',mm:'%d minutes',h:'an hour',hh:'%d hours',d:'a day',dd:'%d days',M:'a month',MM:'%d months',y:'a year',yy:'%d years'};function relative__relativeTime(number,withoutSuffix,string,isFuture){var output=this._relativeTime[string];return(typeof output==='function')?output(number,withoutSuffix,string,isFuture):output.replace(/%d/i,number);}
function pastFuture(diff,output){var format=this._relativeTime[diff>0?'future':'past'];return typeof format==='function'?format(output):format.replace(/%s/i,output);}
function locale_set__set(config){var prop,i;for(i in config){prop=config[i];if(typeof prop==='function'){this[i]=prop;}else{this['_'+i]=prop;}}
this._ordinalParseLenient=new RegExp(this._ordinalParse.source+'|'+(/\d{1,2}/).source);}
var prototype__proto=Locale.prototype;prototype__proto._calendar=defaultCalendar;prototype__proto.calendar=locale_calendar__calendar;prototype__proto._longDateFormat=defaultLongDateFormat;prototype__proto.longDateFormat=longDateFormat;prototype__proto._invalidDate=defaultInvalidDate;prototype__proto.invalidDate=invalidDate;prototype__proto._ordinal=defaultOrdinal;prototype__proto.ordinal=ordinal;prototype__proto._ordinalParse=defaultOrdinalParse;prototype__proto.preparse=preParsePostFormat;prototype__proto.postformat=preParsePostFormat;prototype__proto._relativeTime=defaultRelativeTime;prototype__proto.relativeTime=relative__relativeTime;prototype__proto.pastFuture=pastFuture;prototype__proto.set=locale_set__set;prototype__proto.months=localeMonths;prototype__proto._months=defaultLocaleMonths;prototype__proto.monthsShort=localeMonthsShort;prototype__proto._monthsShort=defaultLocaleMonthsShort;prototype__proto.monthsParse=localeMonthsParse;prototype__proto.week=localeWeek;prototype__proto._week=defaultLocaleWeek;prototype__proto.firstDayOfYear=localeFirstDayOfYear;prototype__proto.firstDayOfWeek=localeFirstDayOfWeek;prototype__proto.weekdays=localeWeekdays;prototype__proto._weekdays=defaultLocaleWeekdays;prototype__proto.weekdaysMin=localeWeekdaysMin;prototype__proto._weekdaysMin=defaultLocaleWeekdaysMin;prototype__proto.weekdaysShort=localeWeekdaysShort;prototype__proto._weekdaysShort=defaultLocaleWeekdaysShort;prototype__proto.weekdaysParse=localeWeekdaysParse;prototype__proto.isPM=localeIsPM;prototype__proto._meridiemParse=defaultLocaleMeridiemParse;prototype__proto.meridiem=localeMeridiem;function lists__get(format,index,field,setter){var locale=locale_locales__getLocale();var utc=create_utc__createUTC().set(setter,index);return locale[field](utc,format);}
function list(format,index,field,count,setter){if(typeof format==='number'){index=format;format=undefined;}
format=format||'';if(index!=null){return lists__get(format,index,field,setter);}
var i;var out=[];for(i=0;i<count;i++){out[i]=lists__get(format,i,field,setter);}
return out;}
function lists__listMonths(format,index){return list(format,index,'months',12,'month');}
function lists__listMonthsShort(format,index){return list(format,index,'monthsShort',12,'month');}
function lists__listWeekdays(format,index){return list(format,index,'weekdays',7,'day');}
function lists__listWeekdaysShort(format,index){return list(format,index,'weekdaysShort',7,'day');}
function lists__listWeekdaysMin(format,index){return list(format,index,'weekdaysMin',7,'day');}
locale_locales__getSetGlobalLocale('en',{ordinalParse:/\d{1,2}(th|st|nd|rd)/,ordinal:function(number){var b=number%10,output=(toInt(number%100/10)===1)?'th':(b===1)?'st':(b===2)?'nd':(b===3)?'rd':'th';return number+output;}});utils_hooks__hooks.lang=deprecate('moment.lang is deprecated. Use moment.locale instead.',locale_locales__getSetGlobalLocale);utils_hooks__hooks.langData=deprecate('moment.langData is deprecated. Use moment.localeData instead.',locale_locales__getLocale);var mathAbs=Math.abs;function duration_abs__abs(){var data=this._data;this._milliseconds=mathAbs(this._milliseconds);this._days=mathAbs(this._days);this._months=mathAbs(this._months);data.milliseconds=mathAbs(data.milliseconds);data.seconds=mathAbs(data.seconds);data.minutes=mathAbs(data.minutes);data.hours=mathAbs(data.hours);data.months=mathAbs(data.months);data.years=mathAbs(data.years);return this;}
function duration_add_subtract__addSubtract(duration,input,value,direction){var other=create__createDuration(input,value);duration._milliseconds+=direction*other._milliseconds;duration._days+=direction*other._days;duration._months+=direction*other._months;return duration._bubble();}
function duration_add_subtract__add(input,value){return duration_add_subtract__addSubtract(this,input,value,1);}
function duration_add_subtract__subtract(input,value){return duration_add_subtract__addSubtract(this,input,value,-1);}
function absCeil(number){if(number<0){return Math.floor(number);}else{return Math.ceil(number);}}
function bubble(){var milliseconds=this._milliseconds;var days=this._days;var months=this._months;var data=this._data;var seconds,minutes,hours,years,monthsFromDays;if(!((milliseconds>=0&&days>=0&&months>=0)||(milliseconds<=0&&days<=0&&months<=0))){milliseconds+=absCeil(monthsToDays(months)+days)*864e5;days=0;months=0;}
data.milliseconds=milliseconds%1000;seconds=absFloor(milliseconds/1000);data.seconds=seconds%60;minutes=absFloor(seconds/60);data.minutes=minutes%60;hours=absFloor(minutes/60);data.hours=hours%24;days+=absFloor(hours/24);monthsFromDays=absFloor(daysToMonths(days));months+=monthsFromDays;days-=absCeil(monthsToDays(monthsFromDays));years=absFloor(months/12);months%=12;data.days=days;data.months=months;data.years=years;return this;}
function daysToMonths(days){return days*4800/146097;}
function monthsToDays(months){return months*146097/4800;}
function as(units){var days;var months;var milliseconds=this._milliseconds;units=normalizeUnits(units);if(units==='month'||units==='year'){days=this._days+milliseconds/864e5;months=this._months+daysToMonths(days);return units==='month'?months:months/12;}else{days=this._days+Math.round(monthsToDays(this._months));switch(units){case'week':return days/7+milliseconds/6048e5;case'day':return days+milliseconds/864e5;case'hour':return days*24+milliseconds/36e5;case'minute':return days*1440+milliseconds/6e4;case'second':return days*86400+milliseconds/1000;case'millisecond':return Math.floor(days*864e5)+milliseconds;default:throw new Error('Unknown unit '+units);}}}
function duration_as__valueOf(){return(this._milliseconds+
this._days*864e5+
(this._months%12)*2592e6+
toInt(this._months/12)*31536e6);}
function makeAs(alias){return function(){return this.as(alias);};}
var asMilliseconds=makeAs('ms');var asSeconds=makeAs('s');var asMinutes=makeAs('m');var asHours=makeAs('h');var asDays=makeAs('d');var asWeeks=makeAs('w');var asMonths=makeAs('M');var asYears=makeAs('y');function duration_get__get(units){units=normalizeUnits(units);return this[units+'s']();}
function makeGetter(name){return function(){return this._data[name];};}
var milliseconds=makeGetter('milliseconds');var seconds=makeGetter('seconds');var minutes=makeGetter('minutes');var hours=makeGetter('hours');var days=makeGetter('days');var months=makeGetter('months');var years=makeGetter('years');function weeks(){return absFloor(this.days()/7);}
var round=Math.round;var thresholds={s:45,m:45,h:22,d:26,M:11};function substituteTimeAgo(string,number,withoutSuffix,isFuture,locale){return locale.relativeTime(number||1,!!withoutSuffix,string,isFuture);}
function duration_humanize__relativeTime(posNegDuration,withoutSuffix,locale){var duration=create__createDuration(posNegDuration).abs();var seconds=round(duration.as('s'));var minutes=round(duration.as('m'));var hours=round(duration.as('h'));var days=round(duration.as('d'));var months=round(duration.as('M'));var years=round(duration.as('y'));var a=seconds<thresholds.s&&['s',seconds]||minutes===1&&['m']||minutes<thresholds.m&&['mm',minutes]||hours===1&&['h']||hours<thresholds.h&&['hh',hours]||days===1&&['d']||days<thresholds.d&&['dd',days]||months===1&&['M']||months<thresholds.M&&['MM',months]||years===1&&['y']||['yy',years];a[2]=withoutSuffix;a[3]=+posNegDuration>0;a[4]=locale;return substituteTimeAgo.apply(null,a);}
function duration_humanize__getSetRelativeTimeThreshold(threshold,limit){if(thresholds[threshold]===undefined){return false;}
if(limit===undefined){return thresholds[threshold];}
thresholds[threshold]=limit;return true;}
function humanize(withSuffix){var locale=this.localeData();var output=duration_humanize__relativeTime(this,!withSuffix,locale);if(withSuffix){output=locale.pastFuture(+this,output);}
return locale.postformat(output);}
var iso_string__abs=Math.abs;function iso_string__toISOString(){var seconds=iso_string__abs(this._milliseconds)/1000;var days=iso_string__abs(this._days);var months=iso_string__abs(this._months);var minutes,hours,years;minutes=absFloor(seconds/60);hours=absFloor(minutes/60);seconds%=60;minutes%=60;years=absFloor(months/12);months%=12;var Y=years;var M=months;var D=days;var h=hours;var m=minutes;var s=seconds;var total=this.asSeconds();if(!total){return'P0D';}
return(total<0?'-':'')+'P'+
(Y?Y+'Y':'')+
(M?M+'M':'')+
(D?D+'D':'')+
((h||m||s)?'T':'')+
(h?h+'H':'')+
(m?m+'M':'')+
(s?s+'S':'');}
var duration_prototype__proto=Duration.prototype;duration_prototype__proto.abs=duration_abs__abs;duration_prototype__proto.add=duration_add_subtract__add;duration_prototype__proto.subtract=duration_add_subtract__subtract;duration_prototype__proto.as=as;duration_prototype__proto.asMilliseconds=asMilliseconds;duration_prototype__proto.asSeconds=asSeconds;duration_prototype__proto.asMinutes=asMinutes;duration_prototype__proto.asHours=asHours;duration_prototype__proto.asDays=asDays;duration_prototype__proto.asWeeks=asWeeks;duration_prototype__proto.asMonths=asMonths;duration_prototype__proto.asYears=asYears;duration_prototype__proto.valueOf=duration_as__valueOf;duration_prototype__proto._bubble=bubble;duration_prototype__proto.get=duration_get__get;duration_prototype__proto.milliseconds=milliseconds;duration_prototype__proto.seconds=seconds;duration_prototype__proto.minutes=minutes;duration_prototype__proto.hours=hours;duration_prototype__proto.days=days;duration_prototype__proto.weeks=weeks;duration_prototype__proto.months=months;duration_prototype__proto.years=years;duration_prototype__proto.humanize=humanize;duration_prototype__proto.toISOString=iso_string__toISOString;duration_prototype__proto.toString=iso_string__toISOString;duration_prototype__proto.toJSON=iso_string__toISOString;duration_prototype__proto.locale=locale;duration_prototype__proto.localeData=localeData;duration_prototype__proto.toIsoString=deprecate('toIsoString() is deprecated. Please use toISOString() instead (notice the capitals)',iso_string__toISOString);duration_prototype__proto.lang=lang;addFormatToken('X',0,0,'unix');addFormatToken('x',0,0,'valueOf');addRegexToken('x',matchSigned);addRegexToken('X',matchTimestamp);addParseToken('X',function(input,array,config){config._d=new Date(parseFloat(input,10)*1000);});addParseToken('x',function(input,array,config){config._d=new Date(toInt(input));});utils_hooks__hooks.version='2.10.6';setHookCallback(local__createLocal);utils_hooks__hooks.fn=momentPrototype;utils_hooks__hooks.min=min;utils_hooks__hooks.max=max;utils_hooks__hooks.utc=create_utc__createUTC;utils_hooks__hooks.unix=moment__createUnix;utils_hooks__hooks.months=lists__listMonths;utils_hooks__hooks.isDate=isDate;utils_hooks__hooks.locale=locale_locales__getSetGlobalLocale;utils_hooks__hooks.invalid=valid__createInvalid;utils_hooks__hooks.duration=create__createDuration;utils_hooks__hooks.isMoment=isMoment;utils_hooks__hooks.weekdays=lists__listWeekdays;utils_hooks__hooks.parseZone=moment__createInZone;utils_hooks__hooks.localeData=locale_locales__getLocale;utils_hooks__hooks.isDuration=isDuration;utils_hooks__hooks.monthsShort=lists__listMonthsShort;utils_hooks__hooks.weekdaysMin=lists__listWeekdaysMin;utils_hooks__hooks.defineLocale=defineLocale;utils_hooks__hooks.weekdaysShort=lists__listWeekdaysShort;utils_hooks__hooks.normalizeUnits=normalizeUnits;utils_hooks__hooks.relativeTimeThreshold=duration_humanize__getSetRelativeTimeThreshold;var _moment=utils_hooks__hooks;return _moment;}));
(function(global,factory){typeof exports==='object'&&typeof module!=='undefined'?factory(require('../moment')):typeof define==='function'&&define.amd?define(['moment'],factory):factory(global.moment)}(this,function(moment){'use strict';function processRelativeTime(number,withoutSuffix,key,isFuture){var format={'m':['eine Minute','einer Minute'],'h':['eine Stunde','einer Stunde'],'d':['ein Tag','einem Tag'],'dd':[number+' Tage',number+' Tagen'],'M':['ein Monat','einem Monat'],'MM':[number+' Monate',number+' Monaten'],'y':['ein Jahr','einem Jahr'],'yy':[number+' Jahre',number+' Jahren']};return withoutSuffix?format[key][0]:format[key][1];}
var de=moment.defineLocale('de',{months:'Januar_Februar_März_April_Mai_Juni_Juli_August_September_Oktober_November_Dezember'.split('_'),monthsShort:'Jan._Febr._Mrz._Apr._Mai_Jun._Jul._Aug._Sept._Okt._Nov._Dez.'.split('_'),weekdays:'Sonntag_Montag_Dienstag_Mittwoch_Donnerstag_Freitag_Samstag'.split('_'),weekdaysShort:'So._Mo._Di._Mi._Do._Fr._Sa.'.split('_'),weekdaysMin:'So_Mo_Di_Mi_Do_Fr_Sa'.split('_'),longDateFormat:{LT:'HH:mm',LTS:'HH:mm:ss',L:'DD.MM.YYYY',LL:'D. MMMM YYYY',LLL:'D. MMMM YYYY HH:mm',LLLL:'dddd, D. MMMM YYYY HH:mm'},calendar:{sameDay:'[Heute um] LT [Uhr]',sameElse:'L',nextDay:'[Morgen um] LT [Uhr]',nextWeek:'dddd [um] LT [Uhr]',lastDay:'[Gestern um] LT [Uhr]',lastWeek:'[letzten] dddd [um] LT [Uhr]'},relativeTime:{future:'in %s',past:'vor %s',s:'ein paar Sekunden',m:processRelativeTime,mm:'%d Minuten',h:processRelativeTime,hh:'%d Stunden',d:processRelativeTime,dd:processRelativeTime,M:processRelativeTime,MM:processRelativeTime,y:processRelativeTime,yy:processRelativeTime},ordinalParse:/\d{1,2}\./,ordinal:'%d.',week:{dow:1,doy:4}});return de;}));
(function(factory){if(typeof define==='function'&&define.amd){define(['jquery','moment'],factory);}
else if(typeof exports==='object'){module.exports=factory(require('jquery'),require('moment'));}
else{factory(jQuery,moment);}})(function($,moment){;;var FC=$.fullCalendar={version:"2.8.0",internalApiVersion:4};var fcViews=FC.views={};$.fn.fullCalendar=function(options){var args=Array.prototype.slice.call(arguments,1);var res=this;this.each(function(i,_element){var element=$(_element);var calendar=element.data('fullCalendar');var singleRes;if(typeof options==='string'){if(calendar&&$.isFunction(calendar[options])){singleRes=calendar[options].apply(calendar,args);if(!i){res=singleRes;}
if(options==='destroy'){element.removeData('fullCalendar');}}}
else if(!calendar){calendar=new Calendar(element,options);element.data('fullCalendar',calendar);calendar.render();}});return res;};var complexOptions=['header','buttonText','buttonIcons','themeButtonIcons'];function mergeOptions(optionObjs){return mergeProps(optionObjs,complexOptions);}
function massageOverrides(input){var overrides={views:input.views||{}};var subObj;$.each(input,function(name,val){if(name!='views'){if($.isPlainObject(val)&&!/(time|duration|interval)$/i.test(name)&&$.inArray(name,complexOptions)==-1){subObj=null;$.each(val,function(subName,subVal){if(/^(month|week|day|default|basic(Week|Day)?|agenda(Week|Day)?)$/.test(subName)){if(!overrides.views[subName]){overrides.views[subName]={};}
overrides.views[subName][name]=subVal;}
else{if(!subObj){subObj={};}
subObj[subName]=subVal;}});if(subObj){overrides[name]=subObj;}}
else{overrides[name]=val;}}});return overrides;};;FC.intersectRanges=intersectRanges;FC.applyAll=applyAll;FC.debounce=debounce;FC.isInt=isInt;FC.htmlEscape=htmlEscape;FC.cssToStr=cssToStr;FC.proxy=proxy;FC.capitaliseFirstLetter=capitaliseFirstLetter;function compensateScroll(rowEls,scrollbarWidths){if(scrollbarWidths.left){rowEls.css({'border-left-width':1,'margin-left':scrollbarWidths.left-1});}
if(scrollbarWidths.right){rowEls.css({'border-right-width':1,'margin-right':scrollbarWidths.right-1});}}
function uncompensateScroll(rowEls){rowEls.css({'margin-left':'','margin-right':'','border-left-width':'','border-right-width':''});}
function disableCursor(){$('body').addClass('fc-not-allowed');}
function enableCursor(){$('body').removeClass('fc-not-allowed');}
function distributeHeight(els,availableHeight,shouldRedistribute){var minOffset1=Math.floor(availableHeight/els.length);var minOffset2=Math.floor(availableHeight-minOffset1*(els.length-1));var flexEls=[];var flexOffsets=[];var flexHeights=[];var usedHeight=0;undistributeHeight(els);els.each(function(i,el){var minOffset=i===els.length-1?minOffset2:minOffset1;var naturalOffset=$(el).outerHeight(true);if(naturalOffset<minOffset){flexEls.push(el);flexOffsets.push(naturalOffset);flexHeights.push($(el).height());}
else{usedHeight+=naturalOffset;}});if(shouldRedistribute){availableHeight-=usedHeight;minOffset1=Math.floor(availableHeight/flexEls.length);minOffset2=Math.floor(availableHeight-minOffset1*(flexEls.length-1));}
$(flexEls).each(function(i,el){var minOffset=i===flexEls.length-1?minOffset2:minOffset1;var naturalOffset=flexOffsets[i];var naturalHeight=flexHeights[i];var newHeight=minOffset-(naturalOffset-naturalHeight);if(naturalOffset<minOffset){$(el).height(newHeight);}});}
function undistributeHeight(els){els.height('');}
function matchCellWidths(els){var maxInnerWidth=0;els.find('> span').each(function(i,innerEl){var innerWidth=$(innerEl).outerWidth();if(innerWidth>maxInnerWidth){maxInnerWidth=innerWidth;}});maxInnerWidth++;els.width(maxInnerWidth);return maxInnerWidth;}
function subtractInnerElHeight(outerEl,innerEl){var both=outerEl.add(innerEl);var diff;both.css({position:'relative',left:-1});diff=outerEl.outerHeight()-innerEl.outerHeight();both.css({position:'',left:''});return diff;}
FC.getOuterRect=getOuterRect;FC.getClientRect=getClientRect;FC.getContentRect=getContentRect;FC.getScrollbarWidths=getScrollbarWidths;function getScrollParent(el){var position=el.css('position'),scrollParent=el.parents().filter(function(){var parent=$(this);return(/(auto|scroll)/).test(parent.css('overflow')+parent.css('overflow-y')+parent.css('overflow-x'));}).eq(0);return position==='fixed'||!scrollParent.length?$(el[0].ownerDocument||document):scrollParent;}
function getOuterRect(el,origin){var offset=el.offset();var left=offset.left-(origin?origin.left:0);var top=offset.top-(origin?origin.top:0);return{left:left,right:left+el.outerWidth(),top:top,bottom:top+el.outerHeight()};}
function getClientRect(el,origin){var offset=el.offset();var scrollbarWidths=getScrollbarWidths(el);var left=offset.left+getCssFloat(el,'border-left-width')+scrollbarWidths.left-(origin?origin.left:0);var top=offset.top+getCssFloat(el,'border-top-width')+scrollbarWidths.top-(origin?origin.top:0);return{left:left,right:left+el[0].clientWidth,top:top,bottom:top+el[0].clientHeight};}
function getContentRect(el,origin){var offset=el.offset();var left=offset.left+getCssFloat(el,'border-left-width')+getCssFloat(el,'padding-left')-
(origin?origin.left:0);var top=offset.top+getCssFloat(el,'border-top-width')+getCssFloat(el,'padding-top')-
(origin?origin.top:0);return{left:left,right:left+el.width(),top:top,bottom:top+el.height()};}
function getScrollbarWidths(el){var leftRightWidth=el.innerWidth()-el[0].clientWidth;var widths={left:0,right:0,top:0,bottom:el.innerHeight()-el[0].clientHeight};if(getIsLeftRtlScrollbars()&&el.css('direction')=='rtl'){widths.left=leftRightWidth;}
else{widths.right=leftRightWidth;}
return widths;}
var _isLeftRtlScrollbars=null;function getIsLeftRtlScrollbars(){if(_isLeftRtlScrollbars===null){_isLeftRtlScrollbars=computeIsLeftRtlScrollbars();}
return _isLeftRtlScrollbars;}
function computeIsLeftRtlScrollbars(){var el=$('<div><div/></div>').css({position:'absolute',top:-1000,left:0,border:0,padding:0,overflow:'scroll',direction:'rtl'}).appendTo('body');var innerEl=el.children();var res=innerEl.offset().left>el.offset().left;el.remove();return res;}
function getCssFloat(el,prop){return parseFloat(el.css(prop))||0;}
FC.preventDefault=preventDefault;function isPrimaryMouseButton(ev){return ev.which==1&&!ev.ctrlKey;}
function getEvX(ev){if(ev.pageX!==undefined){return ev.pageX;}
var touches=ev.originalEvent.touches;if(touches){return touches[0].pageX;}}
function getEvY(ev){if(ev.pageY!==undefined){return ev.pageY;}
var touches=ev.originalEvent.touches;if(touches){return touches[0].pageY;}}
function getEvIsTouch(ev){return/^touch/.test(ev.type);}
function preventSelection(el){el.addClass('fc-unselectable').on('selectstart',preventDefault);}
function preventDefault(ev){ev.preventDefault();}
function bindAnyScroll(handler){if(window.addEventListener){window.addEventListener('scroll',handler,true);return true;}
return false;}
function unbindAnyScroll(handler){if(window.removeEventListener){window.removeEventListener('scroll',handler,true);return true;}
return false;}
FC.intersectRects=intersectRects;function intersectRects(rect1,rect2){var res={left:Math.max(rect1.left,rect2.left),right:Math.min(rect1.right,rect2.right),top:Math.max(rect1.top,rect2.top),bottom:Math.min(rect1.bottom,rect2.bottom)};if(res.left<res.right&&res.top<res.bottom){return res;}
return false;}
function constrainPoint(point,rect){return{left:Math.min(Math.max(point.left,rect.left),rect.right),top:Math.min(Math.max(point.top,rect.top),rect.bottom)};}
function getRectCenter(rect){return{left:(rect.left+rect.right)/2,top:(rect.top+rect.bottom)/2};}
function diffPoints(point1,point2){return{left:point1.left-point2.left,top:point1.top-point2.top};}
FC.parseFieldSpecs=parseFieldSpecs;FC.compareByFieldSpecs=compareByFieldSpecs;FC.compareByFieldSpec=compareByFieldSpec;FC.flexibleCompare=flexibleCompare;function parseFieldSpecs(input){var specs=[];var tokens=[];var i,token;if(typeof input==='string'){tokens=input.split(/\s*,\s*/);}
else if(typeof input==='function'){tokens=[input];}
else if($.isArray(input)){tokens=input;}
for(i=0;i<tokens.length;i++){token=tokens[i];if(typeof token==='string'){specs.push(token.charAt(0)=='-'?{field:token.substring(1),order:-1}:{field:token,order:1});}
else if(typeof token==='function'){specs.push({func:token});}}
return specs;}
function compareByFieldSpecs(obj1,obj2,fieldSpecs){var i;var cmp;for(i=0;i<fieldSpecs.length;i++){cmp=compareByFieldSpec(obj1,obj2,fieldSpecs[i]);if(cmp){return cmp;}}
return 0;}
function compareByFieldSpec(obj1,obj2,fieldSpec){if(fieldSpec.func){return fieldSpec.func(obj1,obj2);}
return flexibleCompare(obj1[fieldSpec.field],obj2[fieldSpec.field])*(fieldSpec.order||1);}
function flexibleCompare(a,b){if(!a&&!b){return 0;}
if(b==null){return-1;}
if(a==null){return 1;}
if($.type(a)==='string'||$.type(b)==='string'){return String(a).localeCompare(String(b));}
return a-b;}
function intersectRanges(subjectRange,constraintRange){var subjectStart=subjectRange.start;var subjectEnd=subjectRange.end;var constraintStart=constraintRange.start;var constraintEnd=constraintRange.end;var segStart,segEnd;var isStart,isEnd;if(subjectEnd>constraintStart&&subjectStart<constraintEnd){if(subjectStart>=constraintStart){segStart=subjectStart.clone();isStart=true;}
else{segStart=constraintStart.clone();isStart=false;}
if(subjectEnd<=constraintEnd){segEnd=subjectEnd.clone();isEnd=true;}
else{segEnd=constraintEnd.clone();isEnd=false;}
return{start:segStart,end:segEnd,isStart:isStart,isEnd:isEnd};}}
FC.computeIntervalUnit=computeIntervalUnit;FC.divideRangeByDuration=divideRangeByDuration;FC.divideDurationByDuration=divideDurationByDuration;FC.multiplyDuration=multiplyDuration;FC.durationHasTime=durationHasTime;var dayIDs=['sun','mon','tue','wed','thu','fri','sat'];var intervalUnits=['year','month','week','day','hour','minute','second','millisecond'];function diffDayTime(a,b){return moment.duration({days:a.clone().stripTime().diff(b.clone().stripTime(),'days'),ms:a.time()-b.time()});}
function diffDay(a,b){return moment.duration({days:a.clone().stripTime().diff(b.clone().stripTime(),'days')});}
function diffByUnit(a,b,unit){return moment.duration(Math.round(a.diff(b,unit,true)),unit);}
function computeIntervalUnit(start,end){var i,unit;var val;for(i=0;i<intervalUnits.length;i++){unit=intervalUnits[i];val=computeRangeAs(unit,start,end);if(val>=1&&isInt(val)){break;}}
return unit;}
function computeRangeAs(unit,start,end){if(end!=null){return end.diff(start,unit,true);}
else if(moment.isDuration(start)){return start.as(unit);}
else{return start.end.diff(start.start,unit,true);}}
function divideRangeByDuration(start,end,dur){var months;if(durationHasTime(dur)){return(end-start)/dur;}
months=dur.asMonths();if(Math.abs(months)>=1&&isInt(months)){return end.diff(start,'months',true)/months;}
return end.diff(start,'days',true)/dur.asDays();}
function divideDurationByDuration(dur1,dur2){var months1,months2;if(durationHasTime(dur1)||durationHasTime(dur2)){return dur1/dur2;}
months1=dur1.asMonths();months2=dur2.asMonths();if(Math.abs(months1)>=1&&isInt(months1)&&Math.abs(months2)>=1&&isInt(months2)){return months1/months2;}
return dur1.asDays()/dur2.asDays();}
function multiplyDuration(dur,n){var months;if(durationHasTime(dur)){return moment.duration(dur*n);}
months=dur.asMonths();if(Math.abs(months)>=1&&isInt(months)){return moment.duration({months:months*n});}
return moment.duration({days:dur.asDays()*n});}
function durationHasTime(dur){return Boolean(dur.hours()||dur.minutes()||dur.seconds()||dur.milliseconds());}
function isNativeDate(input){return Object.prototype.toString.call(input)==='[object Date]'||input instanceof Date;}
function isTimeString(str){return/^\d+\:\d+(?:\:\d+\.?(?:\d{3})?)?$/.test(str);}
FC.log=function(){var console=window.console;if(console&&console.log){return console.log.apply(console,arguments);}};FC.warn=function(){var console=window.console;if(console&&console.warn){return console.warn.apply(console,arguments);}
else{return FC.log.apply(FC,arguments);}};var hasOwnPropMethod={}.hasOwnProperty;function mergeProps(propObjs,complexProps){var dest={};var i,name;var complexObjs;var j,val;var props;if(complexProps){for(i=0;i<complexProps.length;i++){name=complexProps[i];complexObjs=[];for(j=propObjs.length-1;j>=0;j--){val=propObjs[j][name];if(typeof val==='object'){complexObjs.unshift(val);}
else if(val!==undefined){dest[name]=val;break;}}
if(complexObjs.length){dest[name]=mergeProps(complexObjs);}}}
for(i=propObjs.length-1;i>=0;i--){props=propObjs[i];for(name in props){if(!(name in dest)){dest[name]=props[name];}}}
return dest;}
function createObject(proto){var f=function(){};f.prototype=proto;return new f();}
function copyOwnProps(src,dest){for(var name in src){if(hasOwnProp(src,name)){dest[name]=src[name];}}}
function copyNativeMethods(src,dest){var names=['constructor','toString','valueOf'];var i,name;for(i=0;i<names.length;i++){name=names[i];if(src[name]!==Object.prototype[name]){dest[name]=src[name];}}}
function hasOwnProp(obj,name){return hasOwnPropMethod.call(obj,name);}
function isAtomic(val){return/undefined|null|boolean|number|string/.test($.type(val));}
function applyAll(functions,thisObj,args){if($.isFunction(functions)){functions=[functions];}
if(functions){var i;var ret;for(i=0;i<functions.length;i++){ret=functions[i].apply(thisObj,args)||ret;}
return ret;}}
function firstDefined(){for(var i=0;i<arguments.length;i++){if(arguments[i]!==undefined){return arguments[i];}}}
function htmlEscape(s){return(s+'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/'/g,'&#039;').replace(/"/g,'&quot;').replace(/\n/g,'<br />');}
function stripHtmlEntities(text){return text.replace(/&.*?;/g,'');}
function cssToStr(cssProps){var statements=[];$.each(cssProps,function(name,val){if(val!=null){statements.push(name+':'+val);}});return statements.join(';');}
function capitaliseFirstLetter(str){return str.charAt(0).toUpperCase()+str.slice(1);}
function compareNumbers(a,b){return a-b;}
function isInt(n){return n%1===0;}
function proxy(obj,methodName){var method=obj[methodName];return function(){return method.apply(obj,arguments);};}
function debounce(func,wait,immediate){var timeout,args,context,timestamp,result;var later=function(){var last=+new Date()-timestamp;if(last<wait){timeout=setTimeout(later,wait-last);}
else{timeout=null;if(!immediate){result=func.apply(context,args);context=args=null;}}};return function(){context=this;args=arguments;timestamp=+new Date();var callNow=immediate&&!timeout;if(!timeout){timeout=setTimeout(later,wait);}
if(callNow){result=func.apply(context,args);context=args=null;}
return result;};}
function syncThen(promise,thenFunc){if(!promise||!promise.then||promise.state()==='resolved'){return $.when(thenFunc());}
else if(thenFunc){return promise.then(thenFunc);}};;var ambigDateOfMonthRegex=/^\s*\d{4}-\d\d$/;var ambigTimeOrZoneRegex=/^\s*\d{4}-(?:(\d\d-\d\d)|(W\d\d$)|(W\d\d-\d)|(\d\d\d))((T| )(\d\d(:\d\d(:\d\d(\.\d+)?)?)?)?)?$/;var newMomentProto=moment.fn;var oldMomentProto=$.extend({},newMomentProto);var allowValueOptimization;var setUTCValues;var setLocalValues;FC.moment=function(){return makeMoment(arguments);};FC.moment.utc=function(){var mom=makeMoment(arguments,true);if(mom.hasTime()){mom.utc();}
return mom;};FC.moment.parseZone=function(){return makeMoment(arguments,true,true);};function makeMoment(args,parseAsUTC,parseZone){var input=args[0];var isSingleString=args.length==1&&typeof input==='string';var isAmbigTime;var isAmbigZone;var ambigMatch;var mom;if(moment.isMoment(input)){mom=moment.apply(null,args);transferAmbigs(input,mom);}
else if(isNativeDate(input)||input===undefined){mom=moment.apply(null,args);}
else{isAmbigTime=false;isAmbigZone=false;if(isSingleString){if(ambigDateOfMonthRegex.test(input)){input+='-01';args=[input];isAmbigTime=true;isAmbigZone=true;}
else if((ambigMatch=ambigTimeOrZoneRegex.exec(input))){isAmbigTime=!ambigMatch[5];isAmbigZone=true;}}
else if($.isArray(input)){isAmbigZone=true;}
if(parseAsUTC||isAmbigTime){mom=moment.utc.apply(moment,args);}
else{mom=moment.apply(null,args);}
if(isAmbigTime){mom._ambigTime=true;mom._ambigZone=true;}
else if(parseZone){if(isAmbigZone){mom._ambigZone=true;}
else if(isSingleString){if(mom.utcOffset){mom.utcOffset(input);}
else{mom.zone(input);}}}}
mom._fullCalendar=true;return mom;}
newMomentProto.clone=function(){var mom=oldMomentProto.clone.apply(this,arguments);transferAmbigs(this,mom);if(this._fullCalendar){mom._fullCalendar=true;}
return mom;};newMomentProto.week=newMomentProto.weeks=function(input){var weekCalc=(this._locale||this._lang)._fullCalendar_weekCalc;if(input==null&&typeof weekCalc==='function'){return weekCalc(this);}
else if(weekCalc==='ISO'){return oldMomentProto.isoWeek.apply(this,arguments);}
return oldMomentProto.week.apply(this,arguments);};newMomentProto.time=function(time){if(!this._fullCalendar){return oldMomentProto.time.apply(this,arguments);}
if(time==null){return moment.duration({hours:this.hours(),minutes:this.minutes(),seconds:this.seconds(),milliseconds:this.milliseconds()});}
else{this._ambigTime=false;if(!moment.isDuration(time)&&!moment.isMoment(time)){time=moment.duration(time);}
var dayHours=0;if(moment.isDuration(time)){dayHours=Math.floor(time.asDays())*24;}
return this.hours(dayHours+time.hours()).minutes(time.minutes()).seconds(time.seconds()).milliseconds(time.milliseconds());}};newMomentProto.stripTime=function(){var a;if(!this._ambigTime){a=this.toArray();this.utc();setUTCValues(this,a.slice(0,3));this._ambigTime=true;this._ambigZone=true;}
return this;};newMomentProto.hasTime=function(){return!this._ambigTime;};newMomentProto.stripZone=function(){var a,wasAmbigTime;if(!this._ambigZone){a=this.toArray();wasAmbigTime=this._ambigTime;this.utc();setUTCValues(this,a);this._ambigTime=wasAmbigTime||false;this._ambigZone=true;}
return this;};newMomentProto.hasZone=function(){return!this._ambigZone;};newMomentProto.local=function(){var a=this.toArray();var wasAmbigZone=this._ambigZone;oldMomentProto.local.apply(this,arguments);this._ambigTime=false;this._ambigZone=false;if(wasAmbigZone){setLocalValues(this,a);}
return this;};newMomentProto.utc=function(){oldMomentProto.utc.apply(this,arguments);this._ambigTime=false;this._ambigZone=false;return this;};$.each(['zone','utcOffset'],function(i,name){if(oldMomentProto[name]){newMomentProto[name]=function(tzo){if(tzo!=null){this._ambigTime=false;this._ambigZone=false;}
return oldMomentProto[name].apply(this,arguments);};}});newMomentProto.format=function(){if(this._fullCalendar&&arguments[0]){return formatDate(this,arguments[0]);}
if(this._ambigTime){return oldMomentFormat(this,'YYYY-MM-DD');}
if(this._ambigZone){return oldMomentFormat(this,'YYYY-MM-DD[T]HH:mm:ss');}
return oldMomentProto.format.apply(this,arguments);};newMomentProto.toISOString=function(){if(this._ambigTime){return oldMomentFormat(this,'YYYY-MM-DD');}
if(this._ambigZone){return oldMomentFormat(this,'YYYY-MM-DD[T]HH:mm:ss');}
return oldMomentProto.toISOString.apply(this,arguments);};newMomentProto.isWithin=function(start,end){var a=commonlyAmbiguate([this,start,end]);return a[0]>=a[1]&&a[0]<a[2];};newMomentProto.isSame=function(input,units){var a;if(!this._fullCalendar){return oldMomentProto.isSame.apply(this,arguments);}
if(units){a=commonlyAmbiguate([this,input],true);return oldMomentProto.isSame.call(a[0],a[1],units);}
else{input=FC.moment.parseZone(input);return oldMomentProto.isSame.call(this,input)&&Boolean(this._ambigTime)===Boolean(input._ambigTime)&&Boolean(this._ambigZone)===Boolean(input._ambigZone);}};$.each(['isBefore','isAfter'],function(i,methodName){newMomentProto[methodName]=function(input,units){var a;if(!this._fullCalendar){return oldMomentProto[methodName].apply(this,arguments);}
a=commonlyAmbiguate([this,input]);return oldMomentProto[methodName].call(a[0],a[1],units);};});function commonlyAmbiguate(inputs,preserveTime){var anyAmbigTime=false;var anyAmbigZone=false;var len=inputs.length;var moms=[];var i,mom;for(i=0;i<len;i++){mom=inputs[i];if(!moment.isMoment(mom)){mom=FC.moment.parseZone(mom);}
anyAmbigTime=anyAmbigTime||mom._ambigTime;anyAmbigZone=anyAmbigZone||mom._ambigZone;moms.push(mom);}
for(i=0;i<len;i++){mom=moms[i];if(!preserveTime&&anyAmbigTime&&!mom._ambigTime){moms[i]=mom.clone().stripTime();}
else if(anyAmbigZone&&!mom._ambigZone){moms[i]=mom.clone().stripZone();}}
return moms;}
function transferAmbigs(src,dest){if(src._ambigTime){dest._ambigTime=true;}
else if(dest._ambigTime){dest._ambigTime=false;}
if(src._ambigZone){dest._ambigZone=true;}
else if(dest._ambigZone){dest._ambigZone=false;}}
function setMomentValues(mom,a){mom.year(a[0]||0).month(a[1]||0).date(a[2]||0).hours(a[3]||0).minutes(a[4]||0).seconds(a[5]||0).milliseconds(a[6]||0);}
allowValueOptimization='_d'in moment()&&'updateOffset'in moment;setUTCValues=allowValueOptimization?function(mom,a){mom._d.setTime(Date.UTC.apply(Date,a));moment.updateOffset(mom,false);}:setMomentValues;setLocalValues=allowValueOptimization?function(mom,a){mom._d.setTime(+new Date(a[0]||0,a[1]||0,a[2]||0,a[3]||0,a[4]||0,a[5]||0,a[6]||0));moment.updateOffset(mom,false);}:setMomentValues;;;function oldMomentFormat(mom,formatStr){return oldMomentProto.format.call(mom,formatStr);}
function formatDate(date,formatStr){return formatDateWithChunks(date,getFormatStringChunks(formatStr));}
function formatDateWithChunks(date,chunks){var s='';var i;for(i=0;i<chunks.length;i++){s+=formatDateWithChunk(date,chunks[i]);}
return s;}
var tokenOverrides={t:function(date){return oldMomentFormat(date,'a').charAt(0);},T:function(date){return oldMomentFormat(date,'A').charAt(0);}};function formatDateWithChunk(date,chunk){var token;var maybeStr;if(typeof chunk==='string'){return chunk;}
else if((token=chunk.token)){if(tokenOverrides[token]){return tokenOverrides[token](date);}
return oldMomentFormat(date,token);}
else if(chunk.maybe){maybeStr=formatDateWithChunks(date,chunk.maybe);if(maybeStr.match(/[1-9]/)){return maybeStr;}}
return'';}
function formatRange(date1,date2,formatStr,separator,isRTL){var localeData;date1=FC.moment.parseZone(date1);date2=FC.moment.parseZone(date2);localeData=(date1.localeData||date1.lang).call(date1);formatStr=localeData.longDateFormat(formatStr)||formatStr;separator=separator||' - ';return formatRangeWithChunks(date1,date2,getFormatStringChunks(formatStr),separator,isRTL);}
FC.formatRange=formatRange;function formatRangeWithChunks(date1,date2,chunks,separator,isRTL){var unzonedDate1=date1.clone().stripZone();var unzonedDate2=date2.clone().stripZone();var chunkStr;var leftI;var leftStr='';var rightI;var rightStr='';var middleI;var middleStr1='';var middleStr2='';var middleStr='';for(leftI=0;leftI<chunks.length;leftI++){chunkStr=formatSimilarChunk(date1,date2,unzonedDate1,unzonedDate2,chunks[leftI]);if(chunkStr===false){break;}
leftStr+=chunkStr;}
for(rightI=chunks.length-1;rightI>leftI;rightI--){chunkStr=formatSimilarChunk(date1,date2,unzonedDate1,unzonedDate2,chunks[rightI]);if(chunkStr===false){break;}
rightStr=chunkStr+rightStr;}
for(middleI=leftI;middleI<=rightI;middleI++){middleStr1+=formatDateWithChunk(date1,chunks[middleI]);middleStr2+=formatDateWithChunk(date2,chunks[middleI]);}
if(middleStr1||middleStr2){if(isRTL){middleStr=middleStr2+separator+middleStr1;}
else{middleStr=middleStr1+separator+middleStr2;}}
return leftStr+middleStr+rightStr;}
var similarUnitMap={Y:'year',M:'month',D:'day',d:'day',A:'second',a:'second',T:'second',t:'second',H:'second',h:'second',m:'second',s:'second'};function formatSimilarChunk(date1,date2,unzonedDate1,unzonedDate2,chunk){var token;var unit;if(typeof chunk==='string'){return chunk;}
else if((token=chunk.token)){unit=similarUnitMap[token.charAt(0)];if(unit&&unzonedDate1.isSame(unzonedDate2,unit)){return oldMomentFormat(date1,token);}}
return false;}
var formatStringChunkCache={};function getFormatStringChunks(formatStr){if(formatStr in formatStringChunkCache){return formatStringChunkCache[formatStr];}
return(formatStringChunkCache[formatStr]=chunkFormatString(formatStr));}
function chunkFormatString(formatStr){var chunks=[];var chunker=/\[([^\]]*)\]|\(([^\)]*)\)|(LTS|LT|(\w)\4*o?)|([^\w\[\(]+)/g;var match;while((match=chunker.exec(formatStr))){if(match[1]){chunks.push(match[1]);}
else if(match[2]){chunks.push({maybe:chunkFormatString(match[2])});}
else if(match[3]){chunks.push({token:match[3]});}
else if(match[5]){chunks.push(match[5]);}}
return chunks;};;FC.Class=Class;function Class(){}
Class.extend=function(){var len=arguments.length;var i;var members;for(i=0;i<len;i++){members=arguments[i];if(i<len-1){mixIntoClass(this,members);}}
return extendClass(this,members||{});};Class.mixin=function(members){mixIntoClass(this,members);};function extendClass(superClass,members){var subClass;if(hasOwnProp(members,'constructor')){subClass=members.constructor;}
if(typeof subClass!=='function'){subClass=members.constructor=function(){superClass.apply(this,arguments);};}
subClass.prototype=createObject(superClass.prototype);copyOwnProps(members,subClass.prototype);copyNativeMethods(members,subClass.prototype);copyOwnProps(superClass,subClass);return subClass;}
function mixIntoClass(theClass,members){copyOwnProps(members,theClass.prototype);};;var EmitterMixin=FC.EmitterMixin={on:function(types,handler){var intercept=function(ev,extra){return handler.apply(extra.context||this,extra.args||[]);};if(!handler.guid){handler.guid=$.guid++;}
intercept.guid=handler.guid;$(this).on(types,intercept);return this;},off:function(types,handler){$(this).off(types,handler);return this;},trigger:function(types){var args=Array.prototype.slice.call(arguments,1);$(this).triggerHandler(types,{args:args});return this;},triggerWith:function(types,context,args){$(this).triggerHandler(types,{context:context,args:args});return this;}};;;var ListenerMixin=FC.ListenerMixin=(function(){var guid=0;var ListenerMixin={listenerId:null,listenTo:function(other,arg,callback){if(typeof arg==='object'){for(var eventName in arg){if(arg.hasOwnProperty(eventName)){this.listenTo(other,eventName,arg[eventName]);}}}
else if(typeof arg==='string'){other.on(arg+'.'+this.getListenerNamespace(),$.proxy(callback,this));}},stopListeningTo:function(other,eventName){other.off((eventName||'')+'.'+this.getListenerNamespace());},getListenerNamespace:function(){if(this.listenerId==null){this.listenerId=guid++;}
return'_listener'+this.listenerId;}};return ListenerMixin;})();;;var MouseIgnorerMixin={isIgnoringMouse:false,delayUnignoreMouse:null,initMouseIgnoring:function(delay){this.delayUnignoreMouse=debounce(proxy(this,'unignoreMouse'),delay||1000);},tempIgnoreMouse:function(){this.isIgnoringMouse=true;this.delayUnignoreMouse();},unignoreMouse:function(){this.isIgnoringMouse=false;}};;;var Popover=Class.extend(ListenerMixin,{isHidden:true,options:null,el:null,margin:10,constructor:function(options){this.options=options||{};},show:function(){if(this.isHidden){if(!this.el){this.render();}
this.el.show();this.position();this.isHidden=false;this.trigger('show');}},hide:function(){if(!this.isHidden){this.el.hide();this.isHidden=true;this.trigger('hide');}},render:function(){var _this=this;var options=this.options;this.el=$('<div class="fc-popover"/>').addClass(options.className||'').css({top:0,left:0}).append(options.content).appendTo(options.parentEl);this.el.on('click','.fc-close',function(){_this.hide();});if(options.autoHide){this.listenTo($(document),'mousedown',this.documentMousedown);}},documentMousedown:function(ev){if(this.el&&!$(ev.target).closest(this.el).length){this.hide();}},removeElement:function(){this.hide();if(this.el){this.el.remove();this.el=null;}
this.stopListeningTo($(document),'mousedown');},position:function(){var options=this.options;var origin=this.el.offsetParent().offset();var width=this.el.outerWidth();var height=this.el.outerHeight();var windowEl=$(window);var viewportEl=getScrollParent(this.el);var viewportTop;var viewportLeft;var viewportOffset;var top;var left;top=options.top||0;if(options.left!==undefined){left=options.left;}
else if(options.right!==undefined){left=options.right-width;}
else{left=0;}
if(viewportEl.is(window)||viewportEl.is(document)){viewportEl=windowEl;viewportTop=0;viewportLeft=0;}
else{viewportOffset=viewportEl.offset();viewportTop=viewportOffset.top;viewportLeft=viewportOffset.left;}
viewportTop+=windowEl.scrollTop();viewportLeft+=windowEl.scrollLeft();if(options.viewportConstrain!==false){top=Math.min(top,viewportTop+viewportEl.outerHeight()-height-this.margin);top=Math.max(top,viewportTop+this.margin);left=Math.min(left,viewportLeft+viewportEl.outerWidth()-width-this.margin);left=Math.max(left,viewportLeft+this.margin);}
this.el.css({top:top-origin.top,left:left-origin.left});},trigger:function(name){if(this.options[name]){this.options[name].apply(this,Array.prototype.slice.call(arguments,1));}}});;;var CoordCache=FC.CoordCache=Class.extend({els:null,forcedOffsetParentEl:null,origin:null,boundingRect:null,isHorizontal:false,isVertical:false,lefts:null,rights:null,tops:null,bottoms:null,constructor:function(options){this.els=$(options.els);this.isHorizontal=options.isHorizontal;this.isVertical=options.isVertical;this.forcedOffsetParentEl=options.offsetParent?$(options.offsetParent):null;},build:function(){var offsetParentEl=this.forcedOffsetParentEl||this.els.eq(0).offsetParent();this.origin=offsetParentEl.offset();this.boundingRect=this.queryBoundingRect();if(this.isHorizontal){this.buildElHorizontals();}
if(this.isVertical){this.buildElVerticals();}},clear:function(){this.origin=null;this.boundingRect=null;this.lefts=null;this.rights=null;this.tops=null;this.bottoms=null;},ensureBuilt:function(){if(!this.origin){this.build();}},queryBoundingRect:function(){var scrollParentEl=getScrollParent(this.els.eq(0));if(!scrollParentEl.is(document)){return getClientRect(scrollParentEl);}},buildElHorizontals:function(){var lefts=[];var rights=[];this.els.each(function(i,node){var el=$(node);var left=el.offset().left;var width=el.outerWidth();lefts.push(left);rights.push(left+width);});this.lefts=lefts;this.rights=rights;},buildElVerticals:function(){var tops=[];var bottoms=[];this.els.each(function(i,node){var el=$(node);var top=el.offset().top;var height=el.outerHeight();tops.push(top);bottoms.push(top+height);});this.tops=tops;this.bottoms=bottoms;},getHorizontalIndex:function(leftOffset){this.ensureBuilt();var boundingRect=this.boundingRect;var lefts=this.lefts;var rights=this.rights;var len=lefts.length;var i;if(!boundingRect||(leftOffset>=boundingRect.left&&leftOffset<boundingRect.right)){for(i=0;i<len;i++){if(leftOffset>=lefts[i]&&leftOffset<rights[i]){return i;}}}},getVerticalIndex:function(topOffset){this.ensureBuilt();var boundingRect=this.boundingRect;var tops=this.tops;var bottoms=this.bottoms;var len=tops.length;var i;if(!boundingRect||(topOffset>=boundingRect.top&&topOffset<boundingRect.bottom)){for(i=0;i<len;i++){if(topOffset>=tops[i]&&topOffset<bottoms[i]){return i;}}}},getLeftOffset:function(leftIndex){this.ensureBuilt();return this.lefts[leftIndex];},getLeftPosition:function(leftIndex){this.ensureBuilt();return this.lefts[leftIndex]-this.origin.left;},getRightOffset:function(leftIndex){this.ensureBuilt();return this.rights[leftIndex];},getRightPosition:function(leftIndex){this.ensureBuilt();return this.rights[leftIndex]-this.origin.left;},getWidth:function(leftIndex){this.ensureBuilt();return this.rights[leftIndex]-this.lefts[leftIndex];},getTopOffset:function(topIndex){this.ensureBuilt();return this.tops[topIndex];},getTopPosition:function(topIndex){this.ensureBuilt();return this.tops[topIndex]-this.origin.top;},getBottomOffset:function(topIndex){this.ensureBuilt();return this.bottoms[topIndex];},getBottomPosition:function(topIndex){this.ensureBuilt();return this.bottoms[topIndex]-this.origin.top;},getHeight:function(topIndex){this.ensureBuilt();return this.bottoms[topIndex]-this.tops[topIndex];}});;;var DragListener=FC.DragListener=Class.extend(ListenerMixin,MouseIgnorerMixin,{options:null,subjectEl:null,subjectHref:null,originX:null,originY:null,scrollEl:null,isInteracting:false,isDistanceSurpassed:false,isDelayEnded:false,isDragging:false,isTouch:false,delay:null,delayTimeoutId:null,minDistance:null,handleTouchScrollProxy:null,constructor:function(options){this.options=options||{};this.handleTouchScrollProxy=proxy(this,'handleTouchScroll');this.initMouseIgnoring(500);},startInteraction:function(ev,extraOptions){var isTouch=getEvIsTouch(ev);if(ev.type==='mousedown'){if(this.isIgnoringMouse){return;}
else if(!isPrimaryMouseButton(ev)){return;}
else{ev.preventDefault();}}
if(!this.isInteracting){extraOptions=extraOptions||{};this.delay=firstDefined(extraOptions.delay,this.options.delay,0);this.minDistance=firstDefined(extraOptions.distance,this.options.distance,0);this.subjectEl=this.options.subjectEl;this.isInteracting=true;this.isTouch=isTouch;this.isDelayEnded=false;this.isDistanceSurpassed=false;this.originX=getEvX(ev);this.originY=getEvY(ev);this.scrollEl=getScrollParent($(ev.target));this.bindHandlers();this.initAutoScroll();this.handleInteractionStart(ev);this.startDelay(ev);if(!this.minDistance){this.handleDistanceSurpassed(ev);}}},handleInteractionStart:function(ev){this.trigger('interactionStart',ev);},endInteraction:function(ev,isCancelled){if(this.isInteracting){this.endDrag(ev);if(this.delayTimeoutId){clearTimeout(this.delayTimeoutId);this.delayTimeoutId=null;}
this.destroyAutoScroll();this.unbindHandlers();this.isInteracting=false;this.handleInteractionEnd(ev,isCancelled);if(this.isTouch){this.tempIgnoreMouse();}}},handleInteractionEnd:function(ev,isCancelled){this.trigger('interactionEnd',ev,isCancelled||false);},bindHandlers:function(){var _this=this;var touchStartIgnores=1;if(this.isTouch){this.listenTo($(document),{touchmove:this.handleTouchMove,touchend:this.endInteraction,touchcancel:this.endInteraction,touchstart:function(ev){if(touchStartIgnores){touchStartIgnores--;}
else{_this.endInteraction(ev,true);}}});if(!bindAnyScroll(this.handleTouchScrollProxy)&&this.scrollEl){this.listenTo(this.scrollEl,'scroll',this.handleTouchScroll);}}
else{this.listenTo($(document),{mousemove:this.handleMouseMove,mouseup:this.endInteraction});}
this.listenTo($(document),{selectstart:preventDefault,contextmenu:preventDefault});},unbindHandlers:function(){this.stopListeningTo($(document));unbindAnyScroll(this.handleTouchScrollProxy);if(this.scrollEl){this.stopListeningTo(this.scrollEl,'scroll');}},startDrag:function(ev,extraOptions){this.startInteraction(ev,extraOptions);if(!this.isDragging){this.isDragging=true;this.handleDragStart(ev);}},handleDragStart:function(ev){this.trigger('dragStart',ev);this.initHrefHack();},handleMove:function(ev){var dx=getEvX(ev)-this.originX;var dy=getEvY(ev)-this.originY;var minDistance=this.minDistance;var distanceSq;if(!this.isDistanceSurpassed){distanceSq=dx*dx+dy*dy;if(distanceSq>=minDistance*minDistance){this.handleDistanceSurpassed(ev);}}
if(this.isDragging){this.handleDrag(dx,dy,ev);}},handleDrag:function(dx,dy,ev){this.trigger('drag',dx,dy,ev);this.updateAutoScroll(ev);},endDrag:function(ev){if(this.isDragging){this.isDragging=false;this.handleDragEnd(ev);}},handleDragEnd:function(ev){this.trigger('dragEnd',ev);this.destroyHrefHack();},startDelay:function(initialEv){var _this=this;if(this.delay){this.delayTimeoutId=setTimeout(function(){_this.handleDelayEnd(initialEv);},this.delay);}
else{this.handleDelayEnd(initialEv);}},handleDelayEnd:function(initialEv){this.isDelayEnded=true;if(this.isDistanceSurpassed){this.startDrag(initialEv);}},handleDistanceSurpassed:function(ev){this.isDistanceSurpassed=true;if(this.isDelayEnded){this.startDrag(ev);}},handleTouchMove:function(ev){if(this.isDragging){ev.preventDefault();}
this.handleMove(ev);},handleMouseMove:function(ev){this.handleMove(ev);},handleTouchScroll:function(ev){if(!this.isDragging){this.endInteraction(ev,true);}},initHrefHack:function(){var subjectEl=this.subjectEl;if((this.subjectHref=subjectEl?subjectEl.attr('href'):null)){subjectEl.removeAttr('href');}},destroyHrefHack:function(){var subjectEl=this.subjectEl;var subjectHref=this.subjectHref;setTimeout(function(){if(subjectHref){subjectEl.attr('href',subjectHref);}},0);},trigger:function(name){if(this.options[name]){this.options[name].apply(this,Array.prototype.slice.call(arguments,1));}
if(this['_'+name]){this['_'+name].apply(this,Array.prototype.slice.call(arguments,1));}}});;;DragListener.mixin({isAutoScroll:false,scrollBounds:null,scrollTopVel:null,scrollLeftVel:null,scrollIntervalId:null,scrollSensitivity:30,scrollSpeed:200,scrollIntervalMs:50,initAutoScroll:function(){var scrollEl=this.scrollEl;this.isAutoScroll=this.options.scroll&&scrollEl&&!scrollEl.is(window)&&!scrollEl.is(document);if(this.isAutoScroll){this.listenTo(scrollEl,'scroll',debounce(this.handleDebouncedScroll,100));}},destroyAutoScroll:function(){this.endAutoScroll();if(this.isAutoScroll){this.stopListeningTo(this.scrollEl,'scroll');}},computeScrollBounds:function(){if(this.isAutoScroll){this.scrollBounds=getOuterRect(this.scrollEl);}},updateAutoScroll:function(ev){var sensitivity=this.scrollSensitivity;var bounds=this.scrollBounds;var topCloseness,bottomCloseness;var leftCloseness,rightCloseness;var topVel=0;var leftVel=0;if(bounds){topCloseness=(sensitivity-(getEvY(ev)-bounds.top))/sensitivity;bottomCloseness=(sensitivity-(bounds.bottom-getEvY(ev)))/sensitivity;leftCloseness=(sensitivity-(getEvX(ev)-bounds.left))/sensitivity;rightCloseness=(sensitivity-(bounds.right-getEvX(ev)))/sensitivity;if(topCloseness>=0&&topCloseness<=1){topVel=topCloseness*this.scrollSpeed*-1;}
else if(bottomCloseness>=0&&bottomCloseness<=1){topVel=bottomCloseness*this.scrollSpeed;}
if(leftCloseness>=0&&leftCloseness<=1){leftVel=leftCloseness*this.scrollSpeed*-1;}
else if(rightCloseness>=0&&rightCloseness<=1){leftVel=rightCloseness*this.scrollSpeed;}}
this.setScrollVel(topVel,leftVel);},setScrollVel:function(topVel,leftVel){this.scrollTopVel=topVel;this.scrollLeftVel=leftVel;this.constrainScrollVel();if((this.scrollTopVel||this.scrollLeftVel)&&!this.scrollIntervalId){this.scrollIntervalId=setInterval(proxy(this,'scrollIntervalFunc'),this.scrollIntervalMs);}},constrainScrollVel:function(){var el=this.scrollEl;if(this.scrollTopVel<0){if(el.scrollTop()<=0){this.scrollTopVel=0;}}
else if(this.scrollTopVel>0){if(el.scrollTop()+el[0].clientHeight>=el[0].scrollHeight){this.scrollTopVel=0;}}
if(this.scrollLeftVel<0){if(el.scrollLeft()<=0){this.scrollLeftVel=0;}}
else if(this.scrollLeftVel>0){if(el.scrollLeft()+el[0].clientWidth>=el[0].scrollWidth){this.scrollLeftVel=0;}}},scrollIntervalFunc:function(){var el=this.scrollEl;var frac=this.scrollIntervalMs/1000;if(this.scrollTopVel){el.scrollTop(el.scrollTop()+this.scrollTopVel*frac);}
if(this.scrollLeftVel){el.scrollLeft(el.scrollLeft()+this.scrollLeftVel*frac);}
this.constrainScrollVel();if(!this.scrollTopVel&&!this.scrollLeftVel){this.endAutoScroll();}},endAutoScroll:function(){if(this.scrollIntervalId){clearInterval(this.scrollIntervalId);this.scrollIntervalId=null;this.handleScrollEnd();}},handleDebouncedScroll:function(){if(!this.scrollIntervalId){this.handleScrollEnd();}},handleScrollEnd:function(){}});;;var HitDragListener=DragListener.extend({component:null,origHit:null,hit:null,coordAdjust:null,constructor:function(component,options){DragListener.call(this,options);this.component=component;},handleInteractionStart:function(ev){var subjectEl=this.subjectEl;var subjectRect;var origPoint;var point;this.computeCoords();if(ev){origPoint={left:getEvX(ev),top:getEvY(ev)};point=origPoint;if(subjectEl){subjectRect=getOuterRect(subjectEl);point=constrainPoint(point,subjectRect);}
this.origHit=this.queryHit(point.left,point.top);if(subjectEl&&this.options.subjectCenter){if(this.origHit){subjectRect=intersectRects(this.origHit,subjectRect)||subjectRect;}
point=getRectCenter(subjectRect);}
this.coordAdjust=diffPoints(point,origPoint);}
else{this.origHit=null;this.coordAdjust=null;}
DragListener.prototype.handleInteractionStart.apply(this,arguments);},computeCoords:function(){this.component.prepareHits();this.computeScrollBounds();},handleDragStart:function(ev){var hit;DragListener.prototype.handleDragStart.apply(this,arguments);hit=this.queryHit(getEvX(ev),getEvY(ev));if(hit){this.handleHitOver(hit);}},handleDrag:function(dx,dy,ev){var hit;DragListener.prototype.handleDrag.apply(this,arguments);hit=this.queryHit(getEvX(ev),getEvY(ev));if(!isHitsEqual(hit,this.hit)){if(this.hit){this.handleHitOut();}
if(hit){this.handleHitOver(hit);}}},handleDragEnd:function(){this.handleHitDone();DragListener.prototype.handleDragEnd.apply(this,arguments);},handleHitOver:function(hit){var isOrig=isHitsEqual(hit,this.origHit);this.hit=hit;this.trigger('hitOver',this.hit,isOrig,this.origHit);},handleHitOut:function(){if(this.hit){this.trigger('hitOut',this.hit);this.handleHitDone();this.hit=null;}},handleHitDone:function(){if(this.hit){this.trigger('hitDone',this.hit);}},handleInteractionEnd:function(){DragListener.prototype.handleInteractionEnd.apply(this,arguments);this.origHit=null;this.hit=null;this.component.releaseHits();},handleScrollEnd:function(){DragListener.prototype.handleScrollEnd.apply(this,arguments);this.computeCoords();},queryHit:function(left,top){if(this.coordAdjust){left+=this.coordAdjust.left;top+=this.coordAdjust.top;}
return this.component.queryHit(left,top);}});function isHitsEqual(hit0,hit1){if(!hit0&&!hit1){return true;}
if(hit0&&hit1){return hit0.component===hit1.component&&isHitPropsWithin(hit0,hit1)&&isHitPropsWithin(hit1,hit0);}
return false;}
function isHitPropsWithin(subHit,superHit){for(var propName in subHit){if(!/^(component|left|right|top|bottom)$/.test(propName)){if(subHit[propName]!==superHit[propName]){return false;}}}
return true;};;var MouseFollower=Class.extend(ListenerMixin,{options:null,sourceEl:null,el:null,parentEl:null,top0:null,left0:null,y0:null,x0:null,topDelta:null,leftDelta:null,isFollowing:false,isHidden:false,isAnimating:false,constructor:function(sourceEl,options){this.options=options=options||{};this.sourceEl=sourceEl;this.parentEl=options.parentEl?$(options.parentEl):sourceEl.parent();},start:function(ev){if(!this.isFollowing){this.isFollowing=true;this.y0=getEvY(ev);this.x0=getEvX(ev);this.topDelta=0;this.leftDelta=0;if(!this.isHidden){this.updatePosition();}
if(getEvIsTouch(ev)){this.listenTo($(document),'touchmove',this.handleMove);}
else{this.listenTo($(document),'mousemove',this.handleMove);}}},stop:function(shouldRevert,callback){var _this=this;var revertDuration=this.options.revertDuration;function complete(){this.isAnimating=false;_this.removeElement();this.top0=this.left0=null;if(callback){callback();}}
if(this.isFollowing&&!this.isAnimating){this.isFollowing=false;this.stopListeningTo($(document));if(shouldRevert&&revertDuration&&!this.isHidden){this.isAnimating=true;this.el.animate({top:this.top0,left:this.left0},{duration:revertDuration,complete:complete});}
else{complete();}}},getEl:function(){var el=this.el;if(!el){this.sourceEl.width();el=this.el=this.sourceEl.clone().addClass(this.options.additionalClass||'').css({position:'absolute',visibility:'',display:this.isHidden?'none':'',margin:0,right:'auto',bottom:'auto',width:this.sourceEl.width(),height:this.sourceEl.height(),opacity:this.options.opacity||'',zIndex:this.options.zIndex});el.addClass('fc-unselectable');el.appendTo(this.parentEl);}
return el;},removeElement:function(){if(this.el){this.el.remove();this.el=null;}},updatePosition:function(){var sourceOffset;var origin;this.getEl();if(this.top0===null){this.sourceEl.width();sourceOffset=this.sourceEl.offset();origin=this.el.offsetParent().offset();this.top0=sourceOffset.top-origin.top;this.left0=sourceOffset.left-origin.left;}
this.el.css({top:this.top0+this.topDelta,left:this.left0+this.leftDelta});},handleMove:function(ev){this.topDelta=getEvY(ev)-this.y0;this.leftDelta=getEvX(ev)-this.x0;if(!this.isHidden){this.updatePosition();}},hide:function(){if(!this.isHidden){this.isHidden=true;if(this.el){this.el.hide();}}},show:function(){if(this.isHidden){this.isHidden=false;this.updatePosition();this.getEl().show();}}});;;var Grid=FC.Grid=Class.extend(ListenerMixin,MouseIgnorerMixin,{view:null,isRTL:null,start:null,end:null,el:null,elsByFill:null,eventTimeFormat:null,displayEventTime:null,displayEventEnd:null,minResizeDuration:null,largeUnit:null,dayDragListener:null,segDragListener:null,segResizeListener:null,externalDragListener:null,constructor:function(view){this.view=view;this.isRTL=view.opt('isRTL');this.elsByFill={};this.dayDragListener=this.buildDayDragListener();this.initMouseIgnoring();},computeEventTimeFormat:function(){return this.view.opt('smallTimeFormat');},computeDisplayEventTime:function(){return true;},computeDisplayEventEnd:function(){return true;},setRange:function(range){this.start=range.start.clone();this.end=range.end.clone();this.rangeUpdated();this.processRangeOptions();},rangeUpdated:function(){},processRangeOptions:function(){var view=this.view;var displayEventTime;var displayEventEnd;this.eventTimeFormat=view.opt('eventTimeFormat')||view.opt('timeFormat')||this.computeEventTimeFormat();displayEventTime=view.opt('displayEventTime');if(displayEventTime==null){displayEventTime=this.computeDisplayEventTime();}
displayEventEnd=view.opt('displayEventEnd');if(displayEventEnd==null){displayEventEnd=this.computeDisplayEventEnd();}
this.displayEventTime=displayEventTime;this.displayEventEnd=displayEventEnd;},spanToSegs:function(span){},diffDates:function(a,b){if(this.largeUnit){return diffByUnit(a,b,this.largeUnit);}
else{return diffDayTime(a,b);}},prepareHits:function(){},releaseHits:function(){},queryHit:function(leftOffset,topOffset){},getHitSpan:function(hit){},getHitEl:function(hit){},setElement:function(el){this.el=el;preventSelection(el);this.bindDayHandler('touchstart',this.dayTouchStart);this.bindDayHandler('mousedown',this.dayMousedown);this.bindSegHandlers();this.bindGlobalHandlers();},bindDayHandler:function(name,handler){var _this=this;this.el.on(name,function(ev){if(!$(ev.target).is('.fc-event-container *, .fc-more')&&!$(ev.target).closest('.fc-popover').length){return handler.call(_this,ev);}});},removeElement:function(){this.unbindGlobalHandlers();this.clearDragListeners();this.el.remove();},renderSkeleton:function(){},renderDates:function(){},unrenderDates:function(){},bindGlobalHandlers:function(){this.listenTo($(document),{dragstart:this.externalDragStart,sortstart:this.externalDragStart});},unbindGlobalHandlers:function(){this.stopListeningTo($(document));},dayMousedown:function(ev){if(!this.isIgnoringMouse){this.dayDragListener.startInteraction(ev,{});}},dayTouchStart:function(ev){var view=this.view;if(view.isSelected||view.selectedEvent){this.tempIgnoreMouse();}
this.dayDragListener.startInteraction(ev,{delay:this.view.opt('longPressDelay')});},buildDayDragListener:function(){var _this=this;var view=this.view;var isSelectable=view.opt('selectable');var dayClickHit;var selectionSpan;var dragListener=new HitDragListener(this,{scroll:view.opt('dragScroll'),interactionStart:function(){dayClickHit=dragListener.origHit;},dragStart:function(){view.unselect();},hitOver:function(hit,isOrig,origHit){if(origHit){if(!isOrig){dayClickHit=null;}
if(isSelectable){selectionSpan=_this.computeSelection(_this.getHitSpan(origHit),_this.getHitSpan(hit));if(selectionSpan){_this.renderSelection(selectionSpan);}
else if(selectionSpan===false){disableCursor();}}}},hitOut:function(){dayClickHit=null;selectionSpan=null;_this.unrenderSelection();enableCursor();},interactionEnd:function(ev,isCancelled){if(!isCancelled){if(dayClickHit&&!_this.isIgnoringMouse){view.triggerDayClick(_this.getHitSpan(dayClickHit),_this.getHitEl(dayClickHit),ev);}
if(selectionSpan){view.reportSelection(selectionSpan,ev);}
enableCursor();}}});return dragListener;},clearDragListeners:function(){this.dayDragListener.endInteraction();if(this.segDragListener){this.segDragListener.endInteraction();}
if(this.segResizeListener){this.segResizeListener.endInteraction();}
if(this.externalDragListener){this.externalDragListener.endInteraction();}},renderEventLocationHelper:function(eventLocation,sourceSeg){var fakeEvent=this.fabricateHelperEvent(eventLocation,sourceSeg);return this.renderHelper(fakeEvent,sourceSeg);},fabricateHelperEvent:function(eventLocation,sourceSeg){var fakeEvent=sourceSeg?createObject(sourceSeg.event):{};fakeEvent.start=eventLocation.start.clone();fakeEvent.end=eventLocation.end?eventLocation.end.clone():null;fakeEvent.allDay=null;this.view.calendar.normalizeEventDates(fakeEvent);fakeEvent.className=(fakeEvent.className||[]).concat('fc-helper');if(!sourceSeg){fakeEvent.editable=false;}
return fakeEvent;},renderHelper:function(eventLocation,sourceSeg){},unrenderHelper:function(){},renderSelection:function(span){this.renderHighlight(span);},unrenderSelection:function(){this.unrenderHighlight();},computeSelection:function(span0,span1){var span=this.computeSelectionSpan(span0,span1);if(span&&!this.view.calendar.isSelectionSpanAllowed(span)){return false;}
return span;},computeSelectionSpan:function(span0,span1){var dates=[span0.start,span0.end,span1.start,span1.end];dates.sort(compareNumbers);return{start:dates[0].clone(),end:dates[3].clone()};},renderHighlight:function(span){this.renderFill('highlight',this.spanToSegs(span));},unrenderHighlight:function(){this.unrenderFill('highlight');},highlightSegClasses:function(){return['fc-highlight'];},renderBusinessHours:function(){},unrenderBusinessHours:function(){},getNowIndicatorUnit:function(){},renderNowIndicator:function(date){},unrenderNowIndicator:function(){},renderFill:function(type,segs){},unrenderFill:function(type){var el=this.elsByFill[type];if(el){el.remove();delete this.elsByFill[type];}},renderFillSegEls:function(type,segs){var _this=this;var segElMethod=this[type+'SegEl'];var html='';var renderedSegs=[];var i;if(segs.length){for(i=0;i<segs.length;i++){html+=this.fillSegHtml(type,segs[i]);}
$(html).each(function(i,node){var seg=segs[i];var el=$(node);if(segElMethod){el=segElMethod.call(_this,seg,el);}
if(el){el=$(el);if(el.is(_this.fillSegTag)){seg.el=el;renderedSegs.push(seg);}}});}
return renderedSegs;},fillSegTag:'div',fillSegHtml:function(type,seg){var classesMethod=this[type+'SegClasses'];var cssMethod=this[type+'SegCss'];var classes=classesMethod?classesMethod.call(this,seg):[];var css=cssToStr(cssMethod?cssMethod.call(this,seg):{});return'<'+this.fillSegTag+
(classes.length?' class="'+classes.join(' ')+'"':'')+
(css?' style="'+css+'"':'')+' />';},getDayClasses:function(date){var view=this.view;var today=view.calendar.getNow();var classes=['fc-'+dayIDs[date.day()]];if(view.intervalDuration.as('months')==1&&date.month()!=view.intervalStart.month()){classes.push('fc-other-month');}
if(date.isSame(today,'day')){classes.push('fc-today',view.highlightStateClass);}
else if(date<today){classes.push('fc-past');}
else{classes.push('fc-future');}
return classes;}});;;Grid.mixin({mousedOverSeg:null,isDraggingSeg:false,isResizingSeg:false,isDraggingExternal:false,segs:null,renderEvents:function(events){var bgEvents=[];var fgEvents=[];var i;for(i=0;i<events.length;i++){(isBgEvent(events[i])?bgEvents:fgEvents).push(events[i]);}
this.segs=[].concat(this.renderBgEvents(bgEvents),this.renderFgEvents(fgEvents));},renderBgEvents:function(events){var segs=this.eventsToSegs(events);return this.renderBgSegs(segs)||segs;},renderFgEvents:function(events){var segs=this.eventsToSegs(events);return this.renderFgSegs(segs)||segs;},unrenderEvents:function(){this.handleSegMouseout();this.clearDragListeners();this.unrenderFgSegs();this.unrenderBgSegs();this.segs=null;},getEventSegs:function(){return this.segs||[];},renderFgSegs:function(segs){},unrenderFgSegs:function(){},renderFgSegEls:function(segs,disableResizing){var view=this.view;var html='';var renderedSegs=[];var i;if(segs.length){for(i=0;i<segs.length;i++){html+=this.fgSegHtml(segs[i],disableResizing);}
$(html).each(function(i,node){var seg=segs[i];var el=view.resolveEventEl(seg.event,$(node));if(el){el.data('fc-seg',seg);seg.el=el;renderedSegs.push(seg);}});}
return renderedSegs;},fgSegHtml:function(seg,disableResizing){},renderBgSegs:function(segs){return this.renderFill('bgEvent',segs);},unrenderBgSegs:function(){this.unrenderFill('bgEvent');},bgEventSegEl:function(seg,el){return this.view.resolveEventEl(seg.event,el);},bgEventSegClasses:function(seg){var event=seg.event;var source=event.source||{};return['fc-bgevent'].concat(event.className,source.className||[]);},bgEventSegCss:function(seg){return{'background-color':this.getSegSkinCss(seg)['background-color']};},businessHoursSegClasses:function(seg){return['fc-nonbusiness','fc-bgevent'];},bindSegHandlers:function(){this.bindSegHandler('touchstart',this.handleSegTouchStart);this.bindSegHandler('touchend',this.handleSegTouchEnd);this.bindSegHandler('mouseenter',this.handleSegMouseover);this.bindSegHandler('mouseleave',this.handleSegMouseout);this.bindSegHandler('mousedown',this.handleSegMousedown);this.bindSegHandler('click',this.handleSegClick);},bindSegHandler:function(name,handler){var _this=this;this.el.on(name,'.fc-event-container > *',function(ev){var seg=$(this).data('fc-seg');if(seg&&!_this.isDraggingSeg&&!_this.isResizingSeg){return handler.call(_this,seg,ev);}});},handleSegClick:function(seg,ev){return this.view.trigger('eventClick',seg.el[0],seg.event,ev);},handleSegMouseover:function(seg,ev){if(!this.isIgnoringMouse&&!this.mousedOverSeg){this.mousedOverSeg=seg;seg.el.addClass('fc-allow-mouse-resize');this.view.trigger('eventMouseover',seg.el[0],seg.event,ev);}},handleSegMouseout:function(seg,ev){ev=ev||{};if(this.mousedOverSeg){seg=seg||this.mousedOverSeg;this.mousedOverSeg=null;seg.el.removeClass('fc-allow-mouse-resize');this.view.trigger('eventMouseout',seg.el[0],seg.event,ev);}},handleSegMousedown:function(seg,ev){var isResizing=this.startSegResize(seg,ev,{distance:5});if(!isResizing&&this.view.isEventDraggable(seg.event)){this.buildSegDragListener(seg).startInteraction(ev,{distance:5});}},handleSegTouchStart:function(seg,ev){var view=this.view;var event=seg.event;var isSelected=view.isEventSelected(event);var isDraggable=view.isEventDraggable(event);var isResizable=view.isEventResizable(event);var isResizing=false;var dragListener;if(isSelected&&isResizable){isResizing=this.startSegResize(seg,ev);}
if(!isResizing&&(isDraggable||isResizable)){dragListener=isDraggable?this.buildSegDragListener(seg):this.buildSegSelectListener(seg);dragListener.startInteraction(ev,{delay:isSelected?0:this.view.opt('longPressDelay')});}
this.tempIgnoreMouse();},handleSegTouchEnd:function(seg,ev){this.tempIgnoreMouse();},startSegResize:function(seg,ev,dragOptions){if($(ev.target).is('.fc-resizer')){this.buildSegResizeListener(seg,$(ev.target).is('.fc-start-resizer')).startInteraction(ev,dragOptions);return true;}
return false;},buildSegDragListener:function(seg){var _this=this;var view=this.view;var calendar=view.calendar;var el=seg.el;var event=seg.event;var isDragging;var mouseFollower;var dropLocation;if(this.segDragListener){return this.segDragListener;}
var dragListener=this.segDragListener=new HitDragListener(view,{scroll:view.opt('dragScroll'),subjectEl:el,subjectCenter:true,interactionStart:function(ev){isDragging=false;mouseFollower=new MouseFollower(seg.el,{additionalClass:'fc-dragging',parentEl:view.el,opacity:dragListener.isTouch?null:view.opt('dragOpacity'),revertDuration:view.opt('dragRevertDuration'),zIndex:2});mouseFollower.hide();mouseFollower.start(ev);},dragStart:function(ev){if(dragListener.isTouch&&!view.isEventSelected(event)){view.selectEvent(event);}
isDragging=true;_this.handleSegMouseout(seg,ev);_this.segDragStart(seg,ev);view.hideEvent(event);},hitOver:function(hit,isOrig,origHit){var dragHelperEls;if(seg.hit){origHit=seg.hit;}
dropLocation=_this.computeEventDrop(origHit.component.getHitSpan(origHit),hit.component.getHitSpan(hit),event);if(dropLocation&&!calendar.isEventSpanAllowed(_this.eventToSpan(dropLocation),event)){disableCursor();dropLocation=null;}
if(dropLocation&&(dragHelperEls=view.renderDrag(dropLocation,seg))){dragHelperEls.addClass('fc-dragging');if(!dragListener.isTouch){_this.applyDragOpacity(dragHelperEls);}
mouseFollower.hide();}
else{mouseFollower.show();}
if(isOrig){dropLocation=null;}},hitOut:function(){view.unrenderDrag();mouseFollower.show();dropLocation=null;},hitDone:function(){enableCursor();},interactionEnd:function(ev){mouseFollower.stop(!dropLocation,function(){if(isDragging){view.unrenderDrag();view.showEvent(event);_this.segDragStop(seg,ev);}
if(dropLocation){view.reportEventDrop(event,dropLocation,this.largeUnit,el,ev);}});_this.segDragListener=null;}});return dragListener;},buildSegSelectListener:function(seg){var _this=this;var view=this.view;var event=seg.event;if(this.segDragListener){return this.segDragListener;}
var dragListener=this.segDragListener=new DragListener({dragStart:function(ev){if(dragListener.isTouch&&!view.isEventSelected(event)){view.selectEvent(event);}},interactionEnd:function(ev){_this.segDragListener=null;}});return dragListener;},segDragStart:function(seg,ev){this.isDraggingSeg=true;this.view.trigger('eventDragStart',seg.el[0],seg.event,ev,{});},segDragStop:function(seg,ev){this.isDraggingSeg=false;this.view.trigger('eventDragStop',seg.el[0],seg.event,ev,{});},computeEventDrop:function(startSpan,endSpan,event){var calendar=this.view.calendar;var dragStart=startSpan.start;var dragEnd=endSpan.start;var delta;var dropLocation;if(dragStart.hasTime()===dragEnd.hasTime()){delta=this.diffDates(dragEnd,dragStart);if(event.allDay&&durationHasTime(delta)){dropLocation={start:event.start.clone(),end:calendar.getEventEnd(event),allDay:false};calendar.normalizeEventTimes(dropLocation);}
else{dropLocation={start:event.start.clone(),end:event.end?event.end.clone():null,allDay:event.allDay};}
dropLocation.start.add(delta);if(dropLocation.end){dropLocation.end.add(delta);}}
else{dropLocation={start:dragEnd.clone(),end:null,allDay:!dragEnd.hasTime()};}
return dropLocation;},applyDragOpacity:function(els){var opacity=this.view.opt('dragOpacity');if(opacity!=null){els.each(function(i,node){node.style.opacity=opacity;});}},externalDragStart:function(ev,ui){var view=this.view;var el;var accept;if(view.opt('droppable')){el=$((ui?ui.item:null)||ev.target);accept=view.opt('dropAccept');if($.isFunction(accept)?accept.call(el[0],el):el.is(accept)){if(!this.isDraggingExternal){this.listenToExternalDrag(el,ev,ui);}}}},listenToExternalDrag:function(el,ev,ui){var _this=this;var calendar=this.view.calendar;var meta=getDraggedElMeta(el);var dropLocation;var dragListener=_this.externalDragListener=new HitDragListener(this,{interactionStart:function(){_this.isDraggingExternal=true;},hitOver:function(hit){dropLocation=_this.computeExternalDrop(hit.component.getHitSpan(hit),meta);if(dropLocation&&!calendar.isExternalSpanAllowed(_this.eventToSpan(dropLocation),dropLocation,meta.eventProps)){disableCursor();dropLocation=null;}
if(dropLocation){_this.renderDrag(dropLocation);}},hitOut:function(){dropLocation=null;},hitDone:function(){enableCursor();_this.unrenderDrag();},interactionEnd:function(ev){if(dropLocation){_this.view.reportExternalDrop(meta,dropLocation,el,ev,ui);}
_this.isDraggingExternal=false;_this.externalDragListener=null;}});dragListener.startDrag(ev);},computeExternalDrop:function(span,meta){var calendar=this.view.calendar;var dropLocation={start:calendar.applyTimezone(span.start),end:null};if(meta.startTime&&!dropLocation.start.hasTime()){dropLocation.start.time(meta.startTime);}
if(meta.duration){dropLocation.end=dropLocation.start.clone().add(meta.duration);}
return dropLocation;},renderDrag:function(dropLocation,seg){},unrenderDrag:function(){},buildSegResizeListener:function(seg,isStart){var _this=this;var view=this.view;var calendar=view.calendar;var el=seg.el;var event=seg.event;var eventEnd=calendar.getEventEnd(event);var isDragging;var resizeLocation;var dragListener=this.segResizeListener=new HitDragListener(this,{scroll:view.opt('dragScroll'),subjectEl:el,interactionStart:function(){isDragging=false;},dragStart:function(ev){isDragging=true;_this.handleSegMouseout(seg,ev);_this.segResizeStart(seg,ev);},hitOver:function(hit,isOrig,origHit){var origHitSpan=_this.getHitSpan(origHit);var hitSpan=_this.getHitSpan(hit);resizeLocation=isStart?_this.computeEventStartResize(origHitSpan,hitSpan,event):_this.computeEventEndResize(origHitSpan,hitSpan,event);if(resizeLocation){if(!calendar.isEventSpanAllowed(_this.eventToSpan(resizeLocation),event)){disableCursor();resizeLocation=null;}
else if(resizeLocation.start.isSame(event.start)&&resizeLocation.end.isSame(eventEnd)){resizeLocation=null;}}
if(resizeLocation){view.hideEvent(event);_this.renderEventResize(resizeLocation,seg);}},hitOut:function(){resizeLocation=null;},hitDone:function(){_this.unrenderEventResize();view.showEvent(event);enableCursor();},interactionEnd:function(ev){if(isDragging){_this.segResizeStop(seg,ev);}
if(resizeLocation){view.reportEventResize(event,resizeLocation,this.largeUnit,el,ev);}
_this.segResizeListener=null;}});return dragListener;},segResizeStart:function(seg,ev){this.isResizingSeg=true;this.view.trigger('eventResizeStart',seg.el[0],seg.event,ev,{});},segResizeStop:function(seg,ev){this.isResizingSeg=false;this.view.trigger('eventResizeStop',seg.el[0],seg.event,ev,{});},computeEventStartResize:function(startSpan,endSpan,event){return this.computeEventResize('start',startSpan,endSpan,event);},computeEventEndResize:function(startSpan,endSpan,event){return this.computeEventResize('end',startSpan,endSpan,event);},computeEventResize:function(type,startSpan,endSpan,event){var calendar=this.view.calendar;var delta=this.diffDates(endSpan[type],startSpan[type]);var resizeLocation;var defaultDuration;resizeLocation={start:event.start.clone(),end:calendar.getEventEnd(event),allDay:event.allDay};if(resizeLocation.allDay&&durationHasTime(delta)){resizeLocation.allDay=false;calendar.normalizeEventTimes(resizeLocation);}
resizeLocation[type].add(delta);if(!resizeLocation.start.isBefore(resizeLocation.end)){defaultDuration=this.minResizeDuration||(event.allDay?calendar.defaultAllDayEventDuration:calendar.defaultTimedEventDuration);if(type=='start'){resizeLocation.start=resizeLocation.end.clone().subtract(defaultDuration);}
else{resizeLocation.end=resizeLocation.start.clone().add(defaultDuration);}}
return resizeLocation;},renderEventResize:function(range,seg){},unrenderEventResize:function(){},getEventTimeText:function(range,formatStr,displayEnd){if(formatStr==null){formatStr=this.eventTimeFormat;}
if(displayEnd==null){displayEnd=this.displayEventEnd;}
if(this.displayEventTime&&range.start.hasTime()){if(displayEnd&&range.end){return this.view.formatRange(range,formatStr);}
else{return range.start.format(formatStr);}}
return'';},getSegClasses:function(seg,isDraggable,isResizable){var view=this.view;var event=seg.event;var classes=['fc-event',seg.isStart?'fc-start':'fc-not-start',seg.isEnd?'fc-end':'fc-not-end'].concat(event.className,event.source?event.source.className:[]);if(isDraggable){classes.push('fc-draggable');}
if(isResizable){classes.push('fc-resizable');}
if(view.isEventSelected(event)){classes.push('fc-selected');}
return classes;},getSegSkinCss:function(seg){var event=seg.event;var view=this.view;var source=event.source||{};var eventColor=event.color;var sourceColor=source.color;var optionColor=view.opt('eventColor');return{'background-color':event.backgroundColor||eventColor||source.backgroundColor||sourceColor||view.opt('eventBackgroundColor')||optionColor,'border-color':event.borderColor||eventColor||source.borderColor||sourceColor||view.opt('eventBorderColor')||optionColor,color:event.textColor||source.textColor||view.opt('eventTextColor')};},eventToSegs:function(event){return this.eventsToSegs([event]);},eventToSpan:function(event){return this.eventToSpans(event)[0];},eventToSpans:function(event){var range=this.eventToRange(event);return this.eventRangeToSpans(range,event);},eventsToSegs:function(allEvents,segSliceFunc){var _this=this;var eventsById=groupEventsById(allEvents);var segs=[];$.each(eventsById,function(id,events){var ranges=[];var i;for(i=0;i<events.length;i++){ranges.push(_this.eventToRange(events[i]));}
if(isInverseBgEvent(events[0])){ranges=_this.invertRanges(ranges);for(i=0;i<ranges.length;i++){segs.push.apply(segs,_this.eventRangeToSegs(ranges[i],events[0],segSliceFunc));}}
else{for(i=0;i<ranges.length;i++){segs.push.apply(segs,_this.eventRangeToSegs(ranges[i],events[i],segSliceFunc));}}});return segs;},eventToRange:function(event){return{start:event.start.clone().stripZone(),end:(event.end?event.end.clone():this.view.calendar.getDefaultEventEnd(event.allDay!=null?event.allDay:!event.start.hasTime(),event.start)).stripZone()};},eventRangeToSegs:function(range,event,segSliceFunc){var spans=this.eventRangeToSpans(range,event);var segs=[];var i;for(i=0;i<spans.length;i++){segs.push.apply(segs,this.eventSpanToSegs(spans[i],event,segSliceFunc));}
return segs;},eventRangeToSpans:function(range,event){return[$.extend({},range)];},eventSpanToSegs:function(span,event,segSliceFunc){var segs=segSliceFunc?segSliceFunc(span):this.spanToSegs(span);var i,seg;for(i=0;i<segs.length;i++){seg=segs[i];seg.event=event;seg.eventStartMS=+span.start;seg.eventDurationMS=span.end-span.start;}
return segs;},invertRanges:function(ranges){var view=this.view;var viewStart=view.start.clone();var viewEnd=view.end.clone();var inverseRanges=[];var start=viewStart;var i,range;ranges.sort(compareRanges);for(i=0;i<ranges.length;i++){range=ranges[i];if(range.start>start){inverseRanges.push({start:start,end:range.start});}
start=range.end;}
if(start<viewEnd){inverseRanges.push({start:start,end:viewEnd});}
return inverseRanges;},sortEventSegs:function(segs){segs.sort(proxy(this,'compareEventSegs'));},compareEventSegs:function(seg1,seg2){return seg1.eventStartMS-seg2.eventStartMS||seg2.eventDurationMS-seg1.eventDurationMS||seg2.event.allDay-seg1.event.allDay||compareByFieldSpecs(seg1.event,seg2.event,this.view.eventOrderSpecs);}});function isBgEvent(event){var rendering=getEventRendering(event);return rendering==='background'||rendering==='inverse-background';}
FC.isBgEvent=isBgEvent;function isInverseBgEvent(event){return getEventRendering(event)==='inverse-background';}
function getEventRendering(event){return firstDefined((event.source||{}).rendering,event.rendering);}
function groupEventsById(events){var eventsById={};var i,event;for(i=0;i<events.length;i++){event=events[i];(eventsById[event._id]||(eventsById[event._id]=[])).push(event);}
return eventsById;}
function compareRanges(range1,range2){return range1.start-range2.start;}
FC.dataAttrPrefix='';function getDraggedElMeta(el){var prefix=FC.dataAttrPrefix;var eventProps;var startTime;var duration;var stick;if(prefix){prefix+='-';}
eventProps=el.data(prefix+'event')||null;if(eventProps){if(typeof eventProps==='object'){eventProps=$.extend({},eventProps);}
else{eventProps={};}
startTime=eventProps.start;if(startTime==null){startTime=eventProps.time;}
duration=eventProps.duration;stick=eventProps.stick;delete eventProps.start;delete eventProps.time;delete eventProps.duration;delete eventProps.stick;}
if(startTime==null){startTime=el.data(prefix+'start');}
if(startTime==null){startTime=el.data(prefix+'time');}
if(duration==null){duration=el.data(prefix+'duration');}
if(stick==null){stick=el.data(prefix+'stick');}
startTime=startTime!=null?moment.duration(startTime):null;duration=duration!=null?moment.duration(duration):null;stick=Boolean(stick);return{eventProps:eventProps,startTime:startTime,duration:duration,stick:stick};};;var DayTableMixin=FC.DayTableMixin={breakOnWeeks:false,dayDates:null,dayIndices:null,daysPerRow:null,rowCnt:null,colCnt:null,colHeadFormat:null,updateDayTable:function(){var view=this.view;var date=this.start.clone();var dayIndex=-1;var dayIndices=[];var dayDates=[];var daysPerRow;var firstDay;var rowCnt;while(date.isBefore(this.end)){if(view.isHiddenDay(date)){dayIndices.push(dayIndex+0.5);}
else{dayIndex++;dayIndices.push(dayIndex);dayDates.push(date.clone());}
date.add(1,'days');}
if(this.breakOnWeeks){firstDay=dayDates[0].day();for(daysPerRow=1;daysPerRow<dayDates.length;daysPerRow++){if(dayDates[daysPerRow].day()==firstDay){break;}}
rowCnt=Math.ceil(dayDates.length/daysPerRow);}
else{rowCnt=1;daysPerRow=dayDates.length;}
this.dayDates=dayDates;this.dayIndices=dayIndices;this.daysPerRow=daysPerRow;this.rowCnt=rowCnt;this.updateDayTableCols();},updateDayTableCols:function(){this.colCnt=this.computeColCnt();this.colHeadFormat=this.view.opt('columnFormat')||this.computeColHeadFormat();},computeColCnt:function(){return this.daysPerRow;},getCellDate:function(row,col){return this.dayDates[this.getCellDayIndex(row,col)].clone();},getCellRange:function(row,col){var start=this.getCellDate(row,col);var end=start.clone().add(1,'days');return{start:start,end:end};},getCellDayIndex:function(row,col){return row*this.daysPerRow+this.getColDayIndex(col);},getColDayIndex:function(col){if(this.isRTL){return this.colCnt-1-col;}
else{return col;}},getDateDayIndex:function(date){var dayIndices=this.dayIndices;var dayOffset=date.diff(this.start,'days');if(dayOffset<0){return dayIndices[0]-1;}
else if(dayOffset>=dayIndices.length){return dayIndices[dayIndices.length-1]+1;}
else{return dayIndices[dayOffset];}},computeColHeadFormat:function(){if(this.rowCnt>1||this.colCnt>10){return'ddd';}
else if(this.colCnt>1){return this.view.opt('dayOfMonthFormat');}
else{return'dddd';}},sliceRangeByRow:function(range){var daysPerRow=this.daysPerRow;var normalRange=this.view.computeDayRange(range);var rangeFirst=this.getDateDayIndex(normalRange.start);var rangeLast=this.getDateDayIndex(normalRange.end.clone().subtract(1,'days'));var segs=[];var row;var rowFirst,rowLast;var segFirst,segLast;for(row=0;row<this.rowCnt;row++){rowFirst=row*daysPerRow;rowLast=rowFirst+daysPerRow-1;segFirst=Math.max(rangeFirst,rowFirst);segLast=Math.min(rangeLast,rowLast);segFirst=Math.ceil(segFirst);segLast=Math.floor(segLast);if(segFirst<=segLast){segs.push({row:row,firstRowDayIndex:segFirst-rowFirst,lastRowDayIndex:segLast-rowFirst,isStart:segFirst===rangeFirst,isEnd:segLast===rangeLast});}}
return segs;},sliceRangeByDay:function(range){var daysPerRow=this.daysPerRow;var normalRange=this.view.computeDayRange(range);var rangeFirst=this.getDateDayIndex(normalRange.start);var rangeLast=this.getDateDayIndex(normalRange.end.clone().subtract(1,'days'));var segs=[];var row;var rowFirst,rowLast;var i;var segFirst,segLast;for(row=0;row<this.rowCnt;row++){rowFirst=row*daysPerRow;rowLast=rowFirst+daysPerRow-1;for(i=rowFirst;i<=rowLast;i++){segFirst=Math.max(rangeFirst,i);segLast=Math.min(rangeLast,i);segFirst=Math.ceil(segFirst);segLast=Math.floor(segLast);if(segFirst<=segLast){segs.push({row:row,firstRowDayIndex:segFirst-rowFirst,lastRowDayIndex:segLast-rowFirst,isStart:segFirst===rangeFirst,isEnd:segLast===rangeLast});}}}
return segs;},renderHeadHtml:function(){var view=this.view;return''+'<div class="fc-row '+view.widgetHeaderClass+'">'+'<table>'+'<thead>'+
this.renderHeadTrHtml()+'</thead>'+'</table>'+'</div>';},renderHeadIntroHtml:function(){return this.renderIntroHtml();},renderHeadTrHtml:function(){return''+'<tr>'+
(this.isRTL?'':this.renderHeadIntroHtml())+
this.renderHeadDateCellsHtml()+
(this.isRTL?this.renderHeadIntroHtml():'')+'</tr>';},renderHeadDateCellsHtml:function(){var htmls=[];var col,date;for(col=0;col<this.colCnt;col++){date=this.getCellDate(0,col);htmls.push(this.renderHeadDateCellHtml(date));}
return htmls.join('');},renderHeadDateCellHtml:function(date,colspan,otherAttrs){var view=this.view;return''+'<th class="fc-day-header '+view.widgetHeaderClass+' fc-'+dayIDs[date.day()]+'"'+
(this.rowCnt==1?' data-date="'+date.format('YYYY-MM-DD')+'"':'')+
(colspan>1?' colspan="'+colspan+'"':'')+
(otherAttrs?' '+otherAttrs:'')+'>'+
htmlEscape(date.format(this.colHeadFormat))+'</th>';},renderBgTrHtml:function(row){return''+'<tr>'+
(this.isRTL?'':this.renderBgIntroHtml(row))+
this.renderBgCellsHtml(row)+
(this.isRTL?this.renderBgIntroHtml(row):'')+'</tr>';},renderBgIntroHtml:function(row){return this.renderIntroHtml();},renderBgCellsHtml:function(row){var htmls=[];var col,date;for(col=0;col<this.colCnt;col++){date=this.getCellDate(row,col);htmls.push(this.renderBgCellHtml(date));}
return htmls.join('');},renderBgCellHtml:function(date,otherAttrs){var view=this.view;var classes=this.getDayClasses(date);classes.unshift('fc-day',view.widgetContentClass);return'<td class="'+classes.join(' ')+'"'+' data-date="'+date.format('YYYY-MM-DD')+'"'+
(otherAttrs?' '+otherAttrs:'')+'></td>';},renderIntroHtml:function(){},bookendCells:function(trEl){var introHtml=this.renderIntroHtml();if(introHtml){if(this.isRTL){trEl.append(introHtml);}
else{trEl.prepend(introHtml);}}}};;;var DayGrid=FC.DayGrid=Grid.extend(DayTableMixin,{numbersVisible:false,bottomCoordPadding:0,rowEls:null,cellEls:null,helperEls:null,rowCoordCache:null,colCoordCache:null,renderDates:function(isRigid){var view=this.view;var rowCnt=this.rowCnt;var colCnt=this.colCnt;var html='';var row;var col;for(row=0;row<rowCnt;row++){html+=this.renderDayRowHtml(row,isRigid);}
this.el.html(html);this.rowEls=this.el.find('.fc-row');this.cellEls=this.el.find('.fc-day');this.rowCoordCache=new CoordCache({els:this.rowEls,isVertical:true});this.colCoordCache=new CoordCache({els:this.cellEls.slice(0,this.colCnt),isHorizontal:true});for(row=0;row<rowCnt;row++){for(col=0;col<colCnt;col++){view.trigger('dayRender',null,this.getCellDate(row,col),this.getCellEl(row,col));}}},unrenderDates:function(){this.removeSegPopover();},renderBusinessHours:function(){var events=this.view.calendar.getBusinessHoursEvents(true);var segs=this.eventsToSegs(events);this.renderFill('businessHours',segs,'bgevent');},renderDayRowHtml:function(row,isRigid){var view=this.view;var classes=['fc-row','fc-week',view.widgetContentClass];if(isRigid){classes.push('fc-rigid');}
return''+'<div class="'+classes.join(' ')+'">'+'<div class="fc-bg">'+'<table>'+
this.renderBgTrHtml(row)+'</table>'+'</div>'+'<div class="fc-content-skeleton">'+'<table>'+
(this.numbersVisible?'<thead>'+
this.renderNumberTrHtml(row)+'</thead>':'')+'</table>'+'</div>'+'</div>';},renderNumberTrHtml:function(row){return''+'<tr>'+
(this.isRTL?'':this.renderNumberIntroHtml(row))+
this.renderNumberCellsHtml(row)+
(this.isRTL?this.renderNumberIntroHtml(row):'')+'</tr>';},renderNumberIntroHtml:function(row){return this.renderIntroHtml();},renderNumberCellsHtml:function(row){var htmls=[];var col,date;for(col=0;col<this.colCnt;col++){date=this.getCellDate(row,col);htmls.push(this.renderNumberCellHtml(date));}
return htmls.join('');},renderNumberCellHtml:function(date){var classes;if(!this.view.dayNumbersVisible){return'<td/>';}
classes=this.getDayClasses(date);classes.unshift('fc-day-number');return''+'<td class="'+classes.join(' ')+'" data-date="'+date.format()+'">'+
date.date()+'</td>';},computeEventTimeFormat:function(){return this.view.opt('extraSmallTimeFormat');},computeDisplayEventEnd:function(){return this.colCnt==1;},rangeUpdated:function(){this.updateDayTable();},spanToSegs:function(span){var segs=this.sliceRangeByRow(span);var i,seg;for(i=0;i<segs.length;i++){seg=segs[i];if(this.isRTL){seg.leftCol=this.daysPerRow-1-seg.lastRowDayIndex;seg.rightCol=this.daysPerRow-1-seg.firstRowDayIndex;}
else{seg.leftCol=seg.firstRowDayIndex;seg.rightCol=seg.lastRowDayIndex;}}
return segs;},prepareHits:function(){this.colCoordCache.build();this.rowCoordCache.build();this.rowCoordCache.bottoms[this.rowCnt-1]+=this.bottomCoordPadding;},releaseHits:function(){this.colCoordCache.clear();this.rowCoordCache.clear();},queryHit:function(leftOffset,topOffset){var col=this.colCoordCache.getHorizontalIndex(leftOffset);var row=this.rowCoordCache.getVerticalIndex(topOffset);if(row!=null&&col!=null){return this.getCellHit(row,col);}},getHitSpan:function(hit){return this.getCellRange(hit.row,hit.col);},getHitEl:function(hit){return this.getCellEl(hit.row,hit.col);},getCellHit:function(row,col){return{row:row,col:col,component:this,left:this.colCoordCache.getLeftOffset(col),right:this.colCoordCache.getRightOffset(col),top:this.rowCoordCache.getTopOffset(row),bottom:this.rowCoordCache.getBottomOffset(row)};},getCellEl:function(row,col){return this.cellEls.eq(row*this.colCnt+col);},renderDrag:function(eventLocation,seg){this.renderHighlight(this.eventToSpan(eventLocation));if(seg&&!seg.el.closest(this.el).length){return this.renderEventLocationHelper(eventLocation,seg);}},unrenderDrag:function(){this.unrenderHighlight();this.unrenderHelper();},renderEventResize:function(eventLocation,seg){this.renderHighlight(this.eventToSpan(eventLocation));return this.renderEventLocationHelper(eventLocation,seg);},unrenderEventResize:function(){this.unrenderHighlight();this.unrenderHelper();},renderHelper:function(event,sourceSeg){var helperNodes=[];var segs=this.eventToSegs(event);var rowStructs;segs=this.renderFgSegEls(segs);rowStructs=this.renderSegRows(segs);this.rowEls.each(function(row,rowNode){var rowEl=$(rowNode);var skeletonEl=$('<div class="fc-helper-skeleton"><table/></div>');var skeletonTop;if(sourceSeg&&sourceSeg.row===row){skeletonTop=sourceSeg.el.position().top;}
else{skeletonTop=rowEl.find('.fc-content-skeleton tbody').position().top;}
skeletonEl.css('top',skeletonTop).find('table').append(rowStructs[row].tbodyEl);rowEl.append(skeletonEl);helperNodes.push(skeletonEl[0]);});return(this.helperEls=$(helperNodes));},unrenderHelper:function(){if(this.helperEls){this.helperEls.remove();this.helperEls=null;}},fillSegTag:'td',renderFill:function(type,segs,className){var nodes=[];var i,seg;var skeletonEl;segs=this.renderFillSegEls(type,segs);for(i=0;i<segs.length;i++){seg=segs[i];skeletonEl=this.renderFillRow(type,seg,className);this.rowEls.eq(seg.row).append(skeletonEl);nodes.push(skeletonEl[0]);}
this.elsByFill[type]=$(nodes);return segs;},renderFillRow:function(type,seg,className){var colCnt=this.colCnt;var startCol=seg.leftCol;var endCol=seg.rightCol+1;var skeletonEl;var trEl;className=className||type.toLowerCase();skeletonEl=$('<div class="fc-'+className+'-skeleton">'+'<table><tr/></table>'+'</div>');trEl=skeletonEl.find('tr');if(startCol>0){trEl.append('<td colspan="'+startCol+'"/>');}
trEl.append(seg.el.attr('colspan',endCol-startCol));if(endCol<colCnt){trEl.append('<td colspan="'+(colCnt-endCol)+'"/>');}
this.bookendCells(trEl);return skeletonEl;}});;;DayGrid.mixin({rowStructs:null,unrenderEvents:function(){this.removeSegPopover();Grid.prototype.unrenderEvents.apply(this,arguments);},getEventSegs:function(){return Grid.prototype.getEventSegs.call(this).concat(this.popoverSegs||[]);},renderBgSegs:function(segs){var allDaySegs=$.grep(segs,function(seg){return seg.event.allDay;});return Grid.prototype.renderBgSegs.call(this,allDaySegs);},renderFgSegs:function(segs){var rowStructs;segs=this.renderFgSegEls(segs);rowStructs=this.rowStructs=this.renderSegRows(segs);this.rowEls.each(function(i,rowNode){$(rowNode).find('.fc-content-skeleton > table').append(rowStructs[i].tbodyEl);});return segs;},unrenderFgSegs:function(){var rowStructs=this.rowStructs||[];var rowStruct;while((rowStruct=rowStructs.pop())){rowStruct.tbodyEl.remove();}
this.rowStructs=null;},renderSegRows:function(segs){var rowStructs=[];var segRows;var row;segRows=this.groupSegRows(segs);for(row=0;row<segRows.length;row++){rowStructs.push(this.renderSegRow(row,segRows[row]));}
return rowStructs;},fgSegHtml:function(seg,disableResizing){var view=this.view;var event=seg.event;var isDraggable=view.isEventDraggable(event);var isResizableFromStart=!disableResizing&&event.allDay&&seg.isStart&&view.isEventResizableFromStart(event);var isResizableFromEnd=!disableResizing&&event.allDay&&seg.isEnd&&view.isEventResizableFromEnd(event);var classes=this.getSegClasses(seg,isDraggable,isResizableFromStart||isResizableFromEnd);var skinCss=cssToStr(this.getSegSkinCss(seg));var timeHtml='';var timeText;var titleHtml;classes.unshift('fc-day-grid-event','fc-h-event');if(seg.isStart){timeText=this.getEventTimeText(event);if(timeText){timeHtml='<span class="fc-time">'+htmlEscape(timeText)+'</span>';}}
titleHtml='<span class="fc-title">'+
(htmlEscape(event.title||'')||'&nbsp;')+'</span>';return'<a class="'+classes.join(' ')+'"'+
(event.url?' href="'+htmlEscape(event.url)+'"':'')+
(skinCss?' style="'+skinCss+'"':'')+'>'+'<div class="fc-content">'+
(this.isRTL?titleHtml+' '+timeHtml:timeHtml+' '+titleHtml)+'</div>'+
(isResizableFromStart?'<div class="fc-resizer fc-start-resizer" />':'')+
(isResizableFromEnd?'<div class="fc-resizer fc-end-resizer" />':'')+'</a>';},renderSegRow:function(row,rowSegs){var colCnt=this.colCnt;var segLevels=this.buildSegLevels(rowSegs);var levelCnt=Math.max(1,segLevels.length);var tbody=$('<tbody/>');var segMatrix=[];var cellMatrix=[];var loneCellMatrix=[];var i,levelSegs;var col;var tr;var j,seg;var td;function emptyCellsUntil(endCol){while(col<endCol){td=(loneCellMatrix[i-1]||[])[col];if(td){td.attr('rowspan',parseInt(td.attr('rowspan')||1,10)+1);}
else{td=$('<td/>');tr.append(td);}
cellMatrix[i][col]=td;loneCellMatrix[i][col]=td;col++;}}
for(i=0;i<levelCnt;i++){levelSegs=segLevels[i];col=0;tr=$('<tr/>');segMatrix.push([]);cellMatrix.push([]);loneCellMatrix.push([]);if(levelSegs){for(j=0;j<levelSegs.length;j++){seg=levelSegs[j];emptyCellsUntil(seg.leftCol);td=$('<td class="fc-event-container"/>').append(seg.el);if(seg.leftCol!=seg.rightCol){td.attr('colspan',seg.rightCol-seg.leftCol+1);}
else{loneCellMatrix[i][col]=td;}
while(col<=seg.rightCol){cellMatrix[i][col]=td;segMatrix[i][col]=seg;col++;}
tr.append(td);}}
emptyCellsUntil(colCnt);this.bookendCells(tr);tbody.append(tr);}
return{row:row,tbodyEl:tbody,cellMatrix:cellMatrix,segMatrix:segMatrix,segLevels:segLevels,segs:rowSegs};},buildSegLevels:function(segs){var levels=[];var i,seg;var j;this.sortEventSegs(segs);for(i=0;i<segs.length;i++){seg=segs[i];for(j=0;j<levels.length;j++){if(!isDaySegCollision(seg,levels[j])){break;}}
seg.level=j;(levels[j]||(levels[j]=[])).push(seg);}
for(j=0;j<levels.length;j++){levels[j].sort(compareDaySegCols);}
return levels;},groupSegRows:function(segs){var segRows=[];var i;for(i=0;i<this.rowCnt;i++){segRows.push([]);}
for(i=0;i<segs.length;i++){segRows[segs[i].row].push(segs[i]);}
return segRows;}});function isDaySegCollision(seg,otherSegs){var i,otherSeg;for(i=0;i<otherSegs.length;i++){otherSeg=otherSegs[i];if(otherSeg.leftCol<=seg.rightCol&&otherSeg.rightCol>=seg.leftCol){return true;}}
return false;}
function compareDaySegCols(a,b){return a.leftCol-b.leftCol;};;DayGrid.mixin({segPopover:null,popoverSegs:null,removeSegPopover:function(){if(this.segPopover){this.segPopover.hide();}},limitRows:function(levelLimit){var rowStructs=this.rowStructs||[];var row;var rowLevelLimit;for(row=0;row<rowStructs.length;row++){this.unlimitRow(row);if(!levelLimit){rowLevelLimit=false;}
else if(typeof levelLimit==='number'){rowLevelLimit=levelLimit;}
else{rowLevelLimit=this.computeRowLevelLimit(row);}
if(rowLevelLimit!==false){this.limitRow(row,rowLevelLimit);}}},computeRowLevelLimit:function(row){var rowEl=this.rowEls.eq(row);var rowHeight=rowEl.height();var trEls=this.rowStructs[row].tbodyEl.children();var i,trEl;var trHeight;function iterInnerHeights(i,childNode){trHeight=Math.max(trHeight,$(childNode).outerHeight());}
for(i=0;i<trEls.length;i++){trEl=trEls.eq(i).removeClass('fc-limited');trHeight=0;trEl.find('> td > :first-child').each(iterInnerHeights);if(trEl.position().top+trHeight>rowHeight){return i;}}
return false;},limitRow:function(row,levelLimit){var _this=this;var rowStruct=this.rowStructs[row];var moreNodes=[];var col=0;var levelSegs;var cellMatrix;var limitedNodes;var i,seg;var segsBelow;var totalSegsBelow;var colSegsBelow;var td,rowspan;var segMoreNodes;var j;var moreTd,moreWrap,moreLink;function emptyCellsUntil(endCol){while(col<endCol){segsBelow=_this.getCellSegs(row,col,levelLimit);if(segsBelow.length){td=cellMatrix[levelLimit-1][col];moreLink=_this.renderMoreLink(row,col,segsBelow);moreWrap=$('<div/>').append(moreLink);td.append(moreWrap);moreNodes.push(moreWrap[0]);}
col++;}}
if(levelLimit&&levelLimit<rowStruct.segLevels.length){levelSegs=rowStruct.segLevels[levelLimit-1];cellMatrix=rowStruct.cellMatrix;limitedNodes=rowStruct.tbodyEl.children().slice(levelLimit).addClass('fc-limited').get();for(i=0;i<levelSegs.length;i++){seg=levelSegs[i];emptyCellsUntil(seg.leftCol);colSegsBelow=[];totalSegsBelow=0;while(col<=seg.rightCol){segsBelow=this.getCellSegs(row,col,levelLimit);colSegsBelow.push(segsBelow);totalSegsBelow+=segsBelow.length;col++;}
if(totalSegsBelow){td=cellMatrix[levelLimit-1][seg.leftCol];rowspan=td.attr('rowspan')||1;segMoreNodes=[];for(j=0;j<colSegsBelow.length;j++){moreTd=$('<td class="fc-more-cell"/>').attr('rowspan',rowspan);segsBelow=colSegsBelow[j];moreLink=this.renderMoreLink(row,seg.leftCol+j,[seg].concat(segsBelow));moreWrap=$('<div/>').append(moreLink);moreTd.append(moreWrap);segMoreNodes.push(moreTd[0]);moreNodes.push(moreTd[0]);}
td.addClass('fc-limited').after($(segMoreNodes));limitedNodes.push(td[0]);}}
emptyCellsUntil(this.colCnt);rowStruct.moreEls=$(moreNodes);rowStruct.limitedEls=$(limitedNodes);}},unlimitRow:function(row){var rowStruct=this.rowStructs[row];if(rowStruct.moreEls){rowStruct.moreEls.remove();rowStruct.moreEls=null;}
if(rowStruct.limitedEls){rowStruct.limitedEls.removeClass('fc-limited');rowStruct.limitedEls=null;}},renderMoreLink:function(row,col,hiddenSegs){var _this=this;var view=this.view;return $('<a class="fc-more"/>').text(this.getMoreLinkText(hiddenSegs.length)).on('click',function(ev){var clickOption=view.opt('eventLimitClick');var date=_this.getCellDate(row,col);var moreEl=$(this);var dayEl=_this.getCellEl(row,col);var allSegs=_this.getCellSegs(row,col);var reslicedAllSegs=_this.resliceDaySegs(allSegs,date);var reslicedHiddenSegs=_this.resliceDaySegs(hiddenSegs,date);if(typeof clickOption==='function'){clickOption=view.trigger('eventLimitClick',null,{date:date,dayEl:dayEl,moreEl:moreEl,segs:reslicedAllSegs,hiddenSegs:reslicedHiddenSegs},ev);}
if(clickOption==='popover'){_this.showSegPopover(row,col,moreEl,reslicedAllSegs);}
else if(typeof clickOption==='string'){view.calendar.zoomTo(date,clickOption);}});},showSegPopover:function(row,col,moreLink,segs){var _this=this;var view=this.view;var moreWrap=moreLink.parent();var topEl;var options;if(this.rowCnt==1){topEl=view.el;}
else{topEl=this.rowEls.eq(row);}
options={className:'fc-more-popover',content:this.renderSegPopoverContent(row,col,segs),parentEl:this.el,top:topEl.offset().top,autoHide:true,viewportConstrain:view.opt('popoverViewportConstrain'),hide:function(){_this.segPopover.removeElement();_this.segPopover=null;_this.popoverSegs=null;}};if(this.isRTL){options.right=moreWrap.offset().left+moreWrap.outerWidth()+1;}
else{options.left=moreWrap.offset().left-1;}
this.segPopover=new Popover(options);this.segPopover.show();},renderSegPopoverContent:function(row,col,segs){var view=this.view;var isTheme=view.opt('theme');var title=this.getCellDate(row,col).format(view.opt('dayPopoverFormat'));var content=$('<div class="fc-header '+view.widgetHeaderClass+'">'+'<span class="fc-close '+
(isTheme?'ui-icon ui-icon-closethick':'fc-icon fc-icon-x')+'"></span>'+'<span class="fc-title">'+
htmlEscape(title)+'</span>'+'<div class="fc-clear"/>'+'</div>'+'<div class="fc-body '+view.widgetContentClass+'">'+'<div class="fc-event-container"></div>'+'</div>');var segContainer=content.find('.fc-event-container');var i;segs=this.renderFgSegEls(segs,true);this.popoverSegs=segs;for(i=0;i<segs.length;i++){this.prepareHits();segs[i].hit=this.getCellHit(row,col);this.releaseHits();segContainer.append(segs[i].el);}
return content;},resliceDaySegs:function(segs,dayDate){var events=$.map(segs,function(seg){return seg.event;});var dayStart=dayDate.clone();var dayEnd=dayStart.clone().add(1,'days');var dayRange={start:dayStart,end:dayEnd};segs=this.eventsToSegs(events,function(range){var seg=intersectRanges(range,dayRange);return seg?[seg]:[];});this.sortEventSegs(segs);return segs;},getMoreLinkText:function(num){var opt=this.view.opt('eventLimitText');if(typeof opt==='function'){return opt(num);}
else{return'+'+num+' '+opt;}},getCellSegs:function(row,col,startLevel){var segMatrix=this.rowStructs[row].segMatrix;var level=startLevel||0;var segs=[];var seg;while(level<segMatrix.length){seg=segMatrix[level][col];if(seg){segs.push(seg);}
level++;}
return segs;}});;;var TimeGrid=FC.TimeGrid=Grid.extend(DayTableMixin,{slotDuration:null,snapDuration:null,snapsPerSlot:null,minTime:null,maxTime:null,labelFormat:null,labelInterval:null,colEls:null,slatContainerEl:null,slatEls:null,nowIndicatorEls:null,colCoordCache:null,slatCoordCache:null,constructor:function(){Grid.apply(this,arguments);this.processOptions();},renderDates:function(){this.el.html(this.renderHtml());this.colEls=this.el.find('.fc-day');this.slatContainerEl=this.el.find('.fc-slats');this.slatEls=this.slatContainerEl.find('tr');this.colCoordCache=new CoordCache({els:this.colEls,isHorizontal:true});this.slatCoordCache=new CoordCache({els:this.slatEls,isVertical:true});this.renderContentSkeleton();},renderHtml:function(){return''+'<div class="fc-bg">'+'<table>'+
this.renderBgTrHtml(0)+'</table>'+'</div>'+'<div class="fc-slats">'+'<table>'+
this.renderSlatRowHtml()+'</table>'+'</div>';},renderSlatRowHtml:function(){var view=this.view;var isRTL=this.isRTL;var html='';var slotTime=moment.duration(+this.minTime);var slotDate;var isLabeled;var axisHtml;while(slotTime<this.maxTime){slotDate=this.start.clone().time(slotTime);isLabeled=isInt(divideDurationByDuration(slotTime,this.labelInterval));axisHtml='<td class="fc-axis fc-time '+view.widgetContentClass+'" '+view.axisStyleAttr()+'>'+
(isLabeled?'<span>'+
htmlEscape(slotDate.format(this.labelFormat))+'</span>':'')+'</td>';html+='<tr data-time="'+slotDate.format('HH:mm:ss')+'"'+
(isLabeled?'':' class="fc-minor"')+'>'+
(!isRTL?axisHtml:'')+'<td class="'+view.widgetContentClass+'"/>'+
(isRTL?axisHtml:'')+"</tr>";slotTime.add(this.slotDuration);}
return html;},processOptions:function(){var view=this.view;var slotDuration=view.opt('slotDuration');var snapDuration=view.opt('snapDuration');var input;slotDuration=moment.duration(slotDuration);snapDuration=snapDuration?moment.duration(snapDuration):slotDuration;this.slotDuration=slotDuration;this.snapDuration=snapDuration;this.snapsPerSlot=slotDuration/snapDuration;this.minResizeDuration=snapDuration;this.minTime=moment.duration(view.opt('minTime'));this.maxTime=moment.duration(view.opt('maxTime'));input=view.opt('slotLabelFormat');if($.isArray(input)){input=input[input.length-1];}
this.labelFormat=input||view.opt('axisFormat')||view.opt('smallTimeFormat');input=view.opt('slotLabelInterval');this.labelInterval=input?moment.duration(input):this.computeLabelInterval(slotDuration);},computeLabelInterval:function(slotDuration){var i;var labelInterval;var slotsPerLabel;for(i=AGENDA_STOCK_SUB_DURATIONS.length-1;i>=0;i--){labelInterval=moment.duration(AGENDA_STOCK_SUB_DURATIONS[i]);slotsPerLabel=divideDurationByDuration(labelInterval,slotDuration);if(isInt(slotsPerLabel)&&slotsPerLabel>1){return labelInterval;}}
return moment.duration(slotDuration);},computeEventTimeFormat:function(){return this.view.opt('noMeridiemTimeFormat');},computeDisplayEventEnd:function(){return true;},prepareHits:function(){this.colCoordCache.build();this.slatCoordCache.build();},releaseHits:function(){this.colCoordCache.clear();},queryHit:function(leftOffset,topOffset){var snapsPerSlot=this.snapsPerSlot;var colCoordCache=this.colCoordCache;var slatCoordCache=this.slatCoordCache;var colIndex=colCoordCache.getHorizontalIndex(leftOffset);var slatIndex=slatCoordCache.getVerticalIndex(topOffset);if(colIndex!=null&&slatIndex!=null){var slatTop=slatCoordCache.getTopOffset(slatIndex);var slatHeight=slatCoordCache.getHeight(slatIndex);var partial=(topOffset-slatTop)/slatHeight;var localSnapIndex=Math.floor(partial*snapsPerSlot);var snapIndex=slatIndex*snapsPerSlot+localSnapIndex;var snapTop=slatTop+(localSnapIndex/snapsPerSlot)*slatHeight;var snapBottom=slatTop+((localSnapIndex+1)/snapsPerSlot)*slatHeight;return{col:colIndex,snap:snapIndex,component:this,left:colCoordCache.getLeftOffset(colIndex),right:colCoordCache.getRightOffset(colIndex),top:snapTop,bottom:snapBottom};}},getHitSpan:function(hit){var start=this.getCellDate(0,hit.col);var time=this.computeSnapTime(hit.snap);var end;start.time(time);end=start.clone().add(this.snapDuration);return{start:start,end:end};},getHitEl:function(hit){return this.colEls.eq(hit.col);},rangeUpdated:function(){this.updateDayTable();},computeSnapTime:function(snapIndex){return moment.duration(this.minTime+this.snapDuration*snapIndex);},spanToSegs:function(span){var segs=this.sliceRangeByTimes(span);var i;for(i=0;i<segs.length;i++){if(this.isRTL){segs[i].col=this.daysPerRow-1-segs[i].dayIndex;}
else{segs[i].col=segs[i].dayIndex;}}
return segs;},sliceRangeByTimes:function(range){var segs=[];var seg;var dayIndex;var dayDate;var dayRange;for(dayIndex=0;dayIndex<this.daysPerRow;dayIndex++){dayDate=this.dayDates[dayIndex].clone();dayRange={start:dayDate.clone().time(this.minTime),end:dayDate.clone().time(this.maxTime)};seg=intersectRanges(range,dayRange);if(seg){seg.dayIndex=dayIndex;segs.push(seg);}}
return segs;},updateSize:function(isResize){this.slatCoordCache.build();if(isResize){this.updateSegVerticals([].concat(this.fgSegs||[],this.bgSegs||[],this.businessSegs||[]));}},getTotalSlatHeight:function(){return this.slatContainerEl.outerHeight();},computeDateTop:function(date,startOfDayDate){return this.computeTimeTop(moment.duration(date-startOfDayDate.clone().stripTime()));},computeTimeTop:function(time){var len=this.slatEls.length;var slatCoverage=(time-this.minTime)/this.slotDuration;var slatIndex;var slatRemainder;slatCoverage=Math.max(0,slatCoverage);slatCoverage=Math.min(len,slatCoverage);slatIndex=Math.floor(slatCoverage);slatIndex=Math.min(slatIndex,len-1);slatRemainder=slatCoverage-slatIndex;return this.slatCoordCache.getTopPosition(slatIndex)+
this.slatCoordCache.getHeight(slatIndex)*slatRemainder;},renderDrag:function(eventLocation,seg){if(seg){return this.renderEventLocationHelper(eventLocation,seg);}
else{this.renderHighlight(this.eventToSpan(eventLocation));}},unrenderDrag:function(){this.unrenderHelper();this.unrenderHighlight();},renderEventResize:function(eventLocation,seg){return this.renderEventLocationHelper(eventLocation,seg);},unrenderEventResize:function(){this.unrenderHelper();},renderHelper:function(event,sourceSeg){return this.renderHelperSegs(this.eventToSegs(event),sourceSeg);},unrenderHelper:function(){this.unrenderHelperSegs();},renderBusinessHours:function(){var events=this.view.calendar.getBusinessHoursEvents();var segs=this.eventsToSegs(events);this.renderBusinessSegs(segs);},unrenderBusinessHours:function(){this.unrenderBusinessSegs();},getNowIndicatorUnit:function(){return'minute';},renderNowIndicator:function(date){var segs=this.spanToSegs({start:date,end:date});var top=this.computeDateTop(date,date);var nodes=[];var i;for(i=0;i<segs.length;i++){nodes.push($('<div class="fc-now-indicator fc-now-indicator-line"></div>').css('top',top).appendTo(this.colContainerEls.eq(segs[i].col))[0]);}
if(segs.length>0){nodes.push($('<div class="fc-now-indicator fc-now-indicator-arrow"></div>').css('top',top).appendTo(this.el.find('.fc-content-skeleton'))[0]);}
this.nowIndicatorEls=$(nodes);},unrenderNowIndicator:function(){if(this.nowIndicatorEls){this.nowIndicatorEls.remove();this.nowIndicatorEls=null;}},renderSelection:function(span){if(this.view.opt('selectHelper')){this.renderEventLocationHelper(span);}
else{this.renderHighlight(span);}},unrenderSelection:function(){this.unrenderHelper();this.unrenderHighlight();},renderHighlight:function(span){this.renderHighlightSegs(this.spanToSegs(span));},unrenderHighlight:function(){this.unrenderHighlightSegs();}});;;TimeGrid.mixin({colContainerEls:null,fgContainerEls:null,bgContainerEls:null,helperContainerEls:null,highlightContainerEls:null,businessContainerEls:null,fgSegs:null,bgSegs:null,helperSegs:null,highlightSegs:null,businessSegs:null,renderContentSkeleton:function(){var cellHtml='';var i;var skeletonEl;for(i=0;i<this.colCnt;i++){cellHtml+='<td>'+'<div class="fc-content-col">'+'<div class="fc-event-container fc-helper-container"></div>'+'<div class="fc-event-container"></div>'+'<div class="fc-highlight-container"></div>'+'<div class="fc-bgevent-container"></div>'+'<div class="fc-business-container"></div>'+'</div>'+'</td>';}
skeletonEl=$('<div class="fc-content-skeleton">'+'<table>'+'<tr>'+cellHtml+'</tr>'+'</table>'+'</div>');this.colContainerEls=skeletonEl.find('.fc-content-col');this.helperContainerEls=skeletonEl.find('.fc-helper-container');this.fgContainerEls=skeletonEl.find('.fc-event-container:not(.fc-helper-container)');this.bgContainerEls=skeletonEl.find('.fc-bgevent-container');this.highlightContainerEls=skeletonEl.find('.fc-highlight-container');this.businessContainerEls=skeletonEl.find('.fc-business-container');this.bookendCells(skeletonEl.find('tr'));this.el.append(skeletonEl);},renderFgSegs:function(segs){segs=this.renderFgSegsIntoContainers(segs,this.fgContainerEls);this.fgSegs=segs;return segs;},unrenderFgSegs:function(){this.unrenderNamedSegs('fgSegs');},renderHelperSegs:function(segs,sourceSeg){var helperEls=[];var i,seg;var sourceEl;segs=this.renderFgSegsIntoContainers(segs,this.helperContainerEls);for(i=0;i<segs.length;i++){seg=segs[i];if(sourceSeg&&sourceSeg.col===seg.col){sourceEl=sourceSeg.el;seg.el.css({left:sourceEl.css('left'),right:sourceEl.css('right'),'margin-left':sourceEl.css('margin-left'),'margin-right':sourceEl.css('margin-right')});}
helperEls.push(seg.el[0]);}
this.helperSegs=segs;return $(helperEls);},unrenderHelperSegs:function(){this.unrenderNamedSegs('helperSegs');},renderBgSegs:function(segs){segs=this.renderFillSegEls('bgEvent',segs);this.updateSegVerticals(segs);this.attachSegsByCol(this.groupSegsByCol(segs),this.bgContainerEls);this.bgSegs=segs;return segs;},unrenderBgSegs:function(){this.unrenderNamedSegs('bgSegs');},renderHighlightSegs:function(segs){segs=this.renderFillSegEls('highlight',segs);this.updateSegVerticals(segs);this.attachSegsByCol(this.groupSegsByCol(segs),this.highlightContainerEls);this.highlightSegs=segs;},unrenderHighlightSegs:function(){this.unrenderNamedSegs('highlightSegs');},renderBusinessSegs:function(segs){segs=this.renderFillSegEls('businessHours',segs);this.updateSegVerticals(segs);this.attachSegsByCol(this.groupSegsByCol(segs),this.businessContainerEls);this.businessSegs=segs;},unrenderBusinessSegs:function(){this.unrenderNamedSegs('businessSegs');},groupSegsByCol:function(segs){var segsByCol=[];var i;for(i=0;i<this.colCnt;i++){segsByCol.push([]);}
for(i=0;i<segs.length;i++){segsByCol[segs[i].col].push(segs[i]);}
return segsByCol;},attachSegsByCol:function(segsByCol,containerEls){var col;var segs;var i;for(col=0;col<this.colCnt;col++){segs=segsByCol[col];for(i=0;i<segs.length;i++){containerEls.eq(col).append(segs[i].el);}}},unrenderNamedSegs:function(propName){var segs=this[propName];var i;if(segs){for(i=0;i<segs.length;i++){segs[i].el.remove();}
this[propName]=null;}},renderFgSegsIntoContainers:function(segs,containerEls){var segsByCol;var col;segs=this.renderFgSegEls(segs);segsByCol=this.groupSegsByCol(segs);for(col=0;col<this.colCnt;col++){this.updateFgSegCoords(segsByCol[col]);}
this.attachSegsByCol(segsByCol,containerEls);return segs;},fgSegHtml:function(seg,disableResizing){var view=this.view;var event=seg.event;var isDraggable=view.isEventDraggable(event);var isResizableFromStart=!disableResizing&&seg.isStart&&view.isEventResizableFromStart(event);var isResizableFromEnd=!disableResizing&&seg.isEnd&&view.isEventResizableFromEnd(event);var classes=this.getSegClasses(seg,isDraggable,isResizableFromStart||isResizableFromEnd);var skinCss=cssToStr(this.getSegSkinCss(seg));var timeText;var fullTimeText;var startTimeText;classes.unshift('fc-time-grid-event','fc-v-event');if(view.isMultiDayEvent(event)){if(seg.isStart||seg.isEnd){timeText=this.getEventTimeText(seg);fullTimeText=this.getEventTimeText(seg,'LT');startTimeText=this.getEventTimeText(seg,null,false);}}else{timeText=this.getEventTimeText(event);fullTimeText=this.getEventTimeText(event,'LT');startTimeText=this.getEventTimeText(event,null,false);}
return'<a class="'+classes.join(' ')+'"'+
(event.url?' href="'+htmlEscape(event.url)+'"':'')+
(skinCss?' style="'+skinCss+'"':'')+'>'+'<div class="fc-content">'+
(timeText?'<div class="fc-time"'+' data-start="'+htmlEscape(startTimeText)+'"'+' data-full="'+htmlEscape(fullTimeText)+'"'+'>'+'<span>'+htmlEscape(timeText)+'</span>'+'</div>':'')+
(event.title?'<div class="fc-title">'+
htmlEscape(event.title)+'</div>':'')+'</div>'+'<div class="fc-bg"/>'+
(isResizableFromEnd?'<div class="fc-resizer fc-end-resizer" />':'')+'</a>';},updateSegVerticals:function(segs){this.computeSegVerticals(segs);this.assignSegVerticals(segs);},computeSegVerticals:function(segs){var i,seg;for(i=0;i<segs.length;i++){seg=segs[i];seg.top=this.computeDateTop(seg.start,seg.start);seg.bottom=this.computeDateTop(seg.end,seg.start);}},assignSegVerticals:function(segs){var i,seg;for(i=0;i<segs.length;i++){seg=segs[i];seg.el.css(this.generateSegVerticalCss(seg));}},generateSegVerticalCss:function(seg){return{top:seg.top,bottom:-seg.bottom};},updateFgSegCoords:function(segs){this.computeSegVerticals(segs);this.computeFgSegHorizontals(segs);this.assignSegVerticals(segs);this.assignFgSegHorizontals(segs);},computeFgSegHorizontals:function(segs){var levels;var level0;var i;this.sortEventSegs(segs);levels=buildSlotSegLevels(segs);computeForwardSlotSegs(levels);if((level0=levels[0])){for(i=0;i<level0.length;i++){computeSlotSegPressures(level0[i]);}
for(i=0;i<level0.length;i++){this.computeFgSegForwardBack(level0[i],0,0);}}},computeFgSegForwardBack:function(seg,seriesBackwardPressure,seriesBackwardCoord){var forwardSegs=seg.forwardSegs;var i;if(seg.forwardCoord===undefined){if(!forwardSegs.length){seg.forwardCoord=1;}
else{this.sortForwardSegs(forwardSegs);this.computeFgSegForwardBack(forwardSegs[0],seriesBackwardPressure+1,seriesBackwardCoord);seg.forwardCoord=forwardSegs[0].backwardCoord;}
seg.backwardCoord=seg.forwardCoord-
(seg.forwardCoord-seriesBackwardCoord)/(seriesBackwardPressure+1);for(i=0;i<forwardSegs.length;i++){this.computeFgSegForwardBack(forwardSegs[i],0,seg.forwardCoord);}}},sortForwardSegs:function(forwardSegs){forwardSegs.sort(proxy(this,'compareForwardSegs'));},compareForwardSegs:function(seg1,seg2){return seg2.forwardPressure-seg1.forwardPressure||(seg1.backwardCoord||0)-(seg2.backwardCoord||0)||this.compareEventSegs(seg1,seg2);},assignFgSegHorizontals:function(segs){var i,seg;for(i=0;i<segs.length;i++){seg=segs[i];seg.el.css(this.generateFgSegHorizontalCss(seg));if(seg.bottom-seg.top<30){seg.el.addClass('fc-short');}}},generateFgSegHorizontalCss:function(seg){var shouldOverlap=this.view.opt('slotEventOverlap');var backwardCoord=seg.backwardCoord;var forwardCoord=seg.forwardCoord;var props=this.generateSegVerticalCss(seg);var left;var right;if(shouldOverlap){forwardCoord=Math.min(1,backwardCoord+(forwardCoord-backwardCoord)*2);}
if(this.isRTL){left=1-forwardCoord;right=backwardCoord;}
else{left=backwardCoord;right=1-forwardCoord;}
props.zIndex=seg.level+1;props.left=left*100+'%';props.right=right*100+'%';if(shouldOverlap&&seg.forwardPressure){props[this.isRTL?'marginLeft':'marginRight']=10*2;}
return props;}});function buildSlotSegLevels(segs){var levels=[];var i,seg;var j;for(i=0;i<segs.length;i++){seg=segs[i];for(j=0;j<levels.length;j++){if(!computeSlotSegCollisions(seg,levels[j]).length){break;}}
seg.level=j;(levels[j]||(levels[j]=[])).push(seg);}
return levels;}
function computeForwardSlotSegs(levels){var i,level;var j,seg;var k;for(i=0;i<levels.length;i++){level=levels[i];for(j=0;j<level.length;j++){seg=level[j];seg.forwardSegs=[];for(k=i+1;k<levels.length;k++){computeSlotSegCollisions(seg,levels[k],seg.forwardSegs);}}}}
function computeSlotSegPressures(seg){var forwardSegs=seg.forwardSegs;var forwardPressure=0;var i,forwardSeg;if(seg.forwardPressure===undefined){for(i=0;i<forwardSegs.length;i++){forwardSeg=forwardSegs[i];computeSlotSegPressures(forwardSeg);forwardPressure=Math.max(forwardPressure,1+forwardSeg.forwardPressure);}
seg.forwardPressure=forwardPressure;}}
function computeSlotSegCollisions(seg,otherSegs,results){results=results||[];for(var i=0;i<otherSegs.length;i++){if(isSlotSegCollision(seg,otherSegs[i])){results.push(otherSegs[i]);}}
return results;}
function isSlotSegCollision(seg1,seg2){return seg1.bottom>seg2.top&&seg1.top<seg2.bottom;};;var View=FC.View=Class.extend(EmitterMixin,ListenerMixin,{type:null,name:null,title:null,calendar:null,options:null,el:null,displaying:null,isSkeletonRendered:false,isEventsRendered:false,start:null,end:null,intervalStart:null,intervalEnd:null,intervalDuration:null,intervalUnit:null,isRTL:false,isSelected:false,selectedEvent:null,eventOrderSpecs:null,widgetHeaderClass:null,widgetContentClass:null,highlightStateClass:null,nextDayThreshold:null,isHiddenDayHash:null,isNowIndicatorRendered:null,initialNowDate:null,initialNowQueriedMs:null,nowIndicatorTimeoutID:null,nowIndicatorIntervalID:null,constructor:function(calendar,type,options,intervalDuration){this.calendar=calendar;this.type=this.name=type;this.options=options;this.intervalDuration=intervalDuration||moment.duration(1,'day');this.nextDayThreshold=moment.duration(this.opt('nextDayThreshold'));this.initThemingProps();this.initHiddenDays();this.isRTL=this.opt('isRTL');this.eventOrderSpecs=parseFieldSpecs(this.opt('eventOrder'));this.initialize();},initialize:function(){},opt:function(name){return this.options[name];},trigger:function(name,thisObj){var calendar=this.calendar;return calendar.trigger.apply(calendar,[name,thisObj||this].concat(Array.prototype.slice.call(arguments,2),[this]));},setDate:function(date){this.setRange(this.computeRange(date));},setRange:function(range){$.extend(this,range);this.updateTitle();},computeRange:function(date){var intervalUnit=computeIntervalUnit(this.intervalDuration);var intervalStart=date.clone().startOf(intervalUnit);var intervalEnd=intervalStart.clone().add(this.intervalDuration);var start,end;if(/year|month|week|day/.test(intervalUnit)){intervalStart.stripTime();intervalEnd.stripTime();}
else{if(!intervalStart.hasTime()){intervalStart=this.calendar.time(0);}
if(!intervalEnd.hasTime()){intervalEnd=this.calendar.time(0);}}
start=intervalStart.clone();start=this.skipHiddenDays(start);end=intervalEnd.clone();end=this.skipHiddenDays(end,-1,true);return{intervalUnit:intervalUnit,intervalStart:intervalStart,intervalEnd:intervalEnd,start:start,end:end};},computePrevDate:function(date){return this.massageCurrentDate(date.clone().startOf(this.intervalUnit).subtract(this.intervalDuration),-1);},computeNextDate:function(date){return this.massageCurrentDate(date.clone().startOf(this.intervalUnit).add(this.intervalDuration));},massageCurrentDate:function(date,direction){if(this.intervalDuration.as('days')<=1){if(this.isHiddenDay(date)){date=this.skipHiddenDays(date,direction);date.startOf('day');}}
return date;},updateTitle:function(){this.title=this.computeTitle();},computeTitle:function(){return this.formatRange({start:this.calendar.applyTimezone(this.intervalStart),end:this.calendar.applyTimezone(this.intervalEnd)},this.opt('titleFormat')||this.computeTitleFormat(),this.opt('titleRangeSeparator'));},computeTitleFormat:function(){if(this.intervalUnit=='year'){return'YYYY';}
else if(this.intervalUnit=='month'){return this.opt('monthYearFormat');}
else if(this.intervalDuration.as('days')>1){return'll';}
else{return'LL';}},formatRange:function(range,formatStr,separator){var end=range.end;if(!end.hasTime()){end=end.clone().subtract(1);}
return formatRange(range.start,end,formatStr,separator,this.opt('isRTL'));},setElement:function(el){this.el=el;this.bindGlobalHandlers();},removeElement:function(){this.clear();if(this.isSkeletonRendered){this.unrenderSkeleton();this.isSkeletonRendered=false;}
this.unbindGlobalHandlers();this.el.remove();},display:function(date){var _this=this;var scrollState=null;if(this.displaying){scrollState=this.queryScroll();}
this.calendar.freezeContentHeight();return syncThen(this.clear(),function(){return(_this.displaying=syncThen(_this.displayView(date),function(){_this.forceScroll(_this.computeInitialScroll(scrollState));_this.calendar.unfreezeContentHeight();_this.triggerRender();}));});},clear:function(){var _this=this;var displaying=this.displaying;if(displaying){return syncThen(displaying,function(){_this.displaying=null;_this.clearEvents();return _this.clearView();});}
else{return $.when();}},displayView:function(date){if(!this.isSkeletonRendered){this.renderSkeleton();this.isSkeletonRendered=true;}
if(date){this.setDate(date);}
if(this.render){this.render();}
this.renderDates();this.updateSize();this.renderBusinessHours();this.startNowIndicator();},clearView:function(){this.unselect();this.stopNowIndicator();this.triggerUnrender();this.unrenderBusinessHours();this.unrenderDates();if(this.destroy){this.destroy();}},renderSkeleton:function(){},unrenderSkeleton:function(){},renderDates:function(){},unrenderDates:function(){},triggerRender:function(){this.trigger('viewRender',this,this,this.el);},triggerUnrender:function(){this.trigger('viewDestroy',this,this,this.el);},bindGlobalHandlers:function(){this.listenTo($(document),'mousedown',this.handleDocumentMousedown);this.listenTo($(document),'touchstart',this.processUnselect);},unbindGlobalHandlers:function(){this.stopListeningTo($(document));},initThemingProps:function(){var tm=this.opt('theme')?'ui':'fc';this.widgetHeaderClass=tm+'-widget-header';this.widgetContentClass=tm+'-widget-content';this.highlightStateClass=tm+'-state-highlight';},renderBusinessHours:function(){},unrenderBusinessHours:function(){},startNowIndicator:function(){var _this=this;var unit;var update;var delay;if(this.opt('nowIndicator')){unit=this.getNowIndicatorUnit();if(unit){update=proxy(this,'updateNowIndicator');this.initialNowDate=this.calendar.getNow();this.initialNowQueriedMs=+new Date();this.renderNowIndicator(this.initialNowDate);this.isNowIndicatorRendered=true;delay=this.initialNowDate.clone().startOf(unit).add(1,unit)-this.initialNowDate;this.nowIndicatorTimeoutID=setTimeout(function(){_this.nowIndicatorTimeoutID=null;update();delay=+moment.duration(1,unit);delay=Math.max(100,delay);_this.nowIndicatorIntervalID=setInterval(update,delay);},delay);}}},updateNowIndicator:function(){if(this.isNowIndicatorRendered){this.unrenderNowIndicator();this.renderNowIndicator(this.initialNowDate.clone().add(new Date()-this.initialNowQueriedMs));}},stopNowIndicator:function(){if(this.isNowIndicatorRendered){if(this.nowIndicatorTimeoutID){clearTimeout(this.nowIndicatorTimeoutID);this.nowIndicatorTimeoutID=null;}
if(this.nowIndicatorIntervalID){clearTimeout(this.nowIndicatorIntervalID);this.nowIndicatorIntervalID=null;}
this.unrenderNowIndicator();this.isNowIndicatorRendered=false;}},getNowIndicatorUnit:function(){},renderNowIndicator:function(date){},unrenderNowIndicator:function(){},updateSize:function(isResize){var scrollState;if(isResize){scrollState=this.queryScroll();}
this.updateHeight(isResize);this.updateWidth(isResize);this.updateNowIndicator();if(isResize){this.setScroll(scrollState);}},updateWidth:function(isResize){},updateHeight:function(isResize){var calendar=this.calendar;this.setHeight(calendar.getSuggestedViewHeight(),calendar.isHeightAuto());},setHeight:function(height,isAuto){},computeInitialScroll:function(previousScrollState){return 0;},queryScroll:function(){},setScroll:function(scrollState){},forceScroll:function(scrollState){var _this=this;this.setScroll(scrollState);setTimeout(function(){_this.setScroll(scrollState);},0);},displayEvents:function(events){var scrollState=this.queryScroll();this.clearEvents();this.renderEvents(events);this.isEventsRendered=true;this.setScroll(scrollState);this.triggerEventRender();},clearEvents:function(){var scrollState;if(this.isEventsRendered){scrollState=this.queryScroll();this.triggerEventUnrender();if(this.destroyEvents){this.destroyEvents();}
this.unrenderEvents();this.setScroll(scrollState);this.isEventsRendered=false;}},renderEvents:function(events){},unrenderEvents:function(){},triggerEventRender:function(){this.renderedEventSegEach(function(seg){this.trigger('eventAfterRender',seg.event,seg.event,seg.el);});this.trigger('eventAfterAllRender');},triggerEventUnrender:function(){this.renderedEventSegEach(function(seg){this.trigger('eventDestroy',seg.event,seg.event,seg.el);});},resolveEventEl:function(event,el){var custom=this.trigger('eventRender',event,event,el);if(custom===false){el=null;}
else if(custom&&custom!==true){el=$(custom);}
return el;},showEvent:function(event){this.renderedEventSegEach(function(seg){seg.el.css('visibility','');},event);},hideEvent:function(event){this.renderedEventSegEach(function(seg){seg.el.css('visibility','hidden');},event);},renderedEventSegEach:function(func,event){var segs=this.getEventSegs();var i;for(i=0;i<segs.length;i++){if(!event||segs[i].event._id===event._id){if(segs[i].el){func.call(this,segs[i]);}}}},getEventSegs:function(){return[];},isEventDraggable:function(event){var source=event.source||{};return firstDefined(event.startEditable,source.startEditable,this.opt('eventStartEditable'),event.editable,source.editable,this.opt('editable'));},reportEventDrop:function(event,dropLocation,largeUnit,el,ev){var calendar=this.calendar;var mutateResult=calendar.mutateEvent(event,dropLocation,largeUnit);var undoFunc=function(){mutateResult.undo();calendar.reportEventChange();};this.triggerEventDrop(event,mutateResult.dateDelta,undoFunc,el,ev);calendar.reportEventChange();},triggerEventDrop:function(event,dateDelta,undoFunc,el,ev){this.trigger('eventDrop',el[0],event,dateDelta,undoFunc,ev,{});},reportExternalDrop:function(meta,dropLocation,el,ev,ui){var eventProps=meta.eventProps;var eventInput;var event;if(eventProps){eventInput=$.extend({},eventProps,dropLocation);event=this.calendar.renderEvent(eventInput,meta.stick)[0];}
this.triggerExternalDrop(event,dropLocation,el,ev,ui);},triggerExternalDrop:function(event,dropLocation,el,ev,ui){this.trigger('drop',el[0],dropLocation.start,ev,ui);if(event){this.trigger('eventReceive',null,event);}},renderDrag:function(dropLocation,seg){},unrenderDrag:function(){},isEventResizableFromStart:function(event){return this.opt('eventResizableFromStart')&&this.isEventResizable(event);},isEventResizableFromEnd:function(event){return this.isEventResizable(event);},isEventResizable:function(event){var source=event.source||{};return firstDefined(event.durationEditable,source.durationEditable,this.opt('eventDurationEditable'),event.editable,source.editable,this.opt('editable'));},reportEventResize:function(event,resizeLocation,largeUnit,el,ev){var calendar=this.calendar;var mutateResult=calendar.mutateEvent(event,resizeLocation,largeUnit);var undoFunc=function(){mutateResult.undo();calendar.reportEventChange();};this.triggerEventResize(event,mutateResult.durationDelta,undoFunc,el,ev);calendar.reportEventChange();},triggerEventResize:function(event,durationDelta,undoFunc,el,ev){this.trigger('eventResize',el[0],event,durationDelta,undoFunc,ev,{});},select:function(span,ev){this.unselect(ev);this.renderSelection(span);this.reportSelection(span,ev);},renderSelection:function(span){},reportSelection:function(span,ev){this.isSelected=true;this.triggerSelect(span,ev);},triggerSelect:function(span,ev){this.trigger('select',null,this.calendar.applyTimezone(span.start),this.calendar.applyTimezone(span.end),ev);},unselect:function(ev){if(this.isSelected){this.isSelected=false;if(this.destroySelection){this.destroySelection();}
this.unrenderSelection();this.trigger('unselect',null,ev);}},unrenderSelection:function(){},selectEvent:function(event){if(!this.selectedEvent||this.selectedEvent!==event){this.unselectEvent();this.renderedEventSegEach(function(seg){seg.el.addClass('fc-selected');},event);this.selectedEvent=event;}},unselectEvent:function(){if(this.selectedEvent){this.renderedEventSegEach(function(seg){seg.el.removeClass('fc-selected');},this.selectedEvent);this.selectedEvent=null;}},isEventSelected:function(event){return this.selectedEvent&&this.selectedEvent._id===event._id;},handleDocumentMousedown:function(ev){if(isPrimaryMouseButton(ev)){this.processUnselect(ev);}},processUnselect:function(ev){this.processRangeUnselect(ev);this.processEventUnselect(ev);},processRangeUnselect:function(ev){var ignore;if(this.isSelected&&this.opt('unselectAuto')){ignore=this.opt('unselectCancel');if(!ignore||!$(ev.target).closest(ignore).length){this.unselect(ev);}}},processEventUnselect:function(ev){if(this.selectedEvent){if(!$(ev.target).closest('.fc-selected').length){this.unselectEvent();}}},triggerDayClick:function(span,dayEl,ev){this.trigger('dayClick',dayEl,this.calendar.applyTimezone(span.start),ev);},initHiddenDays:function(){var hiddenDays=this.opt('hiddenDays')||[];var isHiddenDayHash=[];var dayCnt=0;var i;if(this.opt('weekends')===false){hiddenDays.push(0,6);}
for(i=0;i<7;i++){if(!(isHiddenDayHash[i]=$.inArray(i,hiddenDays)!==-1)){dayCnt++;}}
if(!dayCnt){throw'invalid hiddenDays';}
this.isHiddenDayHash=isHiddenDayHash;},isHiddenDay:function(day){if(moment.isMoment(day)){day=day.day();}
return this.isHiddenDayHash[day];},skipHiddenDays:function(date,inc,isExclusive){var out=date.clone();inc=inc||1;while(this.isHiddenDayHash[(out.day()+(isExclusive?inc:0)+7)%7]){out.add(inc,'days');}
return out;},computeDayRange:function(range){var startDay=range.start.clone().stripTime();var end=range.end;var endDay=null;var endTimeMS;if(end){endDay=end.clone().stripTime();endTimeMS=+end.time();if(endTimeMS&&endTimeMS>=this.nextDayThreshold){endDay.add(1,'days');}}
if(!end||endDay<=startDay){endDay=startDay.clone().add(1,'days');}
return{start:startDay,end:endDay};},isMultiDayEvent:function(event){var range=this.computeDayRange(event);return range.end.diff(range.start,'days')>1;}});;;var Scroller=FC.Scroller=Class.extend({el:null,scrollEl:null,overflowX:null,overflowY:null,constructor:function(options){options=options||{};this.overflowX=options.overflowX||options.overflow||'auto';this.overflowY=options.overflowY||options.overflow||'auto';},render:function(){this.el=this.renderEl();this.applyOverflow();},renderEl:function(){return(this.scrollEl=$('<div class="fc-scroller"></div>'));},clear:function(){this.setHeight('auto');this.applyOverflow();},destroy:function(){this.el.remove();},applyOverflow:function(){this.scrollEl.css({'overflow-x':this.overflowX,'overflow-y':this.overflowY});},lockOverflow:function(scrollbarWidths){var overflowX=this.overflowX;var overflowY=this.overflowY;scrollbarWidths=scrollbarWidths||this.getScrollbarWidths();if(overflowX==='auto'){overflowX=(scrollbarWidths.top||scrollbarWidths.bottom||this.scrollEl[0].scrollWidth-1>this.scrollEl[0].clientWidth)?'scroll':'hidden';}
if(overflowY==='auto'){overflowY=(scrollbarWidths.left||scrollbarWidths.right||this.scrollEl[0].scrollHeight-1>this.scrollEl[0].clientHeight)?'scroll':'hidden';}
this.scrollEl.css({'overflow-x':overflowX,'overflow-y':overflowY});},setHeight:function(height){this.scrollEl.height(height);},getScrollTop:function(){return this.scrollEl.scrollTop();},setScrollTop:function(top){this.scrollEl.scrollTop(top);},getClientWidth:function(){return this.scrollEl[0].clientWidth;},getClientHeight:function(){return this.scrollEl[0].clientHeight;},getScrollbarWidths:function(){return getScrollbarWidths(this.scrollEl);}});;;var Calendar=FC.Calendar=Class.extend({dirDefaults:null,langDefaults:null,overrides:null,options:null,viewSpecCache:null,view:null,header:null,loadingLevel:0,constructor:Calendar_constructor,initialize:function(){},initOptions:function(overrides){var lang,langDefaults;var isRTL,dirDefaults;overrides=massageOverrides(overrides);lang=overrides.lang;langDefaults=langOptionHash[lang];if(!langDefaults){lang=Calendar.defaults.lang;langDefaults=langOptionHash[lang]||{};}
isRTL=firstDefined(overrides.isRTL,langDefaults.isRTL,Calendar.defaults.isRTL);dirDefaults=isRTL?Calendar.rtlDefaults:{};this.dirDefaults=dirDefaults;this.langDefaults=langDefaults;this.overrides=overrides;this.options=mergeOptions([Calendar.defaults,dirDefaults,langDefaults,overrides]);populateInstanceComputableOptions(this.options);this.viewSpecCache={};},getViewSpec:function(viewType){var cache=this.viewSpecCache;return cache[viewType]||(cache[viewType]=this.buildViewSpec(viewType));},getUnitViewSpec:function(unit){var viewTypes;var i;var spec;if($.inArray(unit,intervalUnits)!=-1){viewTypes=this.header.getViewsWithButtons();$.each(FC.views,function(viewType){viewTypes.push(viewType);});for(i=0;i<viewTypes.length;i++){spec=this.getViewSpec(viewTypes[i]);if(spec){if(spec.singleUnit==unit){return spec;}}}}},buildViewSpec:function(requestedViewType){var viewOverrides=this.overrides.views||{};var specChain=[];var defaultsChain=[];var overridesChain=[];var viewType=requestedViewType;var spec;var overrides;var duration;var unit;while(viewType){spec=fcViews[viewType];overrides=viewOverrides[viewType];viewType=null;if(typeof spec==='function'){spec={'class':spec};}
if(spec){specChain.unshift(spec);defaultsChain.unshift(spec.defaults||{});duration=duration||spec.duration;viewType=viewType||spec.type;}
if(overrides){overridesChain.unshift(overrides);duration=duration||overrides.duration;viewType=viewType||overrides.type;}}
spec=mergeProps(specChain);spec.type=requestedViewType;if(!spec['class']){return false;}
if(duration){duration=moment.duration(duration);if(duration.valueOf()){spec.duration=duration;unit=computeIntervalUnit(duration);if(duration.as(unit)===1){spec.singleUnit=unit;overridesChain.unshift(viewOverrides[unit]||{});}}}
spec.defaults=mergeOptions(defaultsChain);spec.overrides=mergeOptions(overridesChain);this.buildViewSpecOptions(spec);this.buildViewSpecButtonText(spec,requestedViewType);return spec;},buildViewSpecOptions:function(spec){spec.options=mergeOptions([Calendar.defaults,spec.defaults,this.dirDefaults,this.langDefaults,this.overrides,spec.overrides]);populateInstanceComputableOptions(spec.options);},buildViewSpecButtonText:function(spec,requestedViewType){function queryButtonText(options){var buttonText=options.buttonText||{};return buttonText[requestedViewType]||(spec.singleUnit?buttonText[spec.singleUnit]:null);}
spec.buttonTextOverride=queryButtonText(this.overrides)||spec.overrides.buttonText;spec.buttonTextDefault=queryButtonText(this.langDefaults)||queryButtonText(this.dirDefaults)||spec.defaults.buttonText||queryButtonText(Calendar.defaults)||(spec.duration?this.humanizeDuration(spec.duration):null)||requestedViewType;},instantiateView:function(viewType){var spec=this.getViewSpec(viewType);return new spec['class'](this,viewType,spec.options,spec.duration);},isValidViewType:function(viewType){return Boolean(this.getViewSpec(viewType));},pushLoading:function(){if(!(this.loadingLevel++)){this.trigger('loading',null,true,this.view);}},popLoading:function(){if(!(--this.loadingLevel)){this.trigger('loading',null,false,this.view);}},buildSelectSpan:function(zonedStartInput,zonedEndInput){var start=this.moment(zonedStartInput).stripZone();var end;if(zonedEndInput){end=this.moment(zonedEndInput).stripZone();}
else if(start.hasTime()){end=start.clone().add(this.defaultTimedEventDuration);}
else{end=start.clone().add(this.defaultAllDayEventDuration);}
return{start:start,end:end};}});Calendar.mixin(EmitterMixin);function Calendar_constructor(element,overrides){var t=this;t.initOptions(overrides||{});var options=this.options;t.render=render;t.destroy=destroy;t.refetchEvents=refetchEvents;t.refetchEventSources=refetchEventSources;t.reportEvents=reportEvents;t.reportEventChange=reportEventChange;t.rerenderEvents=renderEvents;t.changeView=renderView;t.select=select;t.unselect=unselect;t.prev=prev;t.next=next;t.prevYear=prevYear;t.nextYear=nextYear;t.today=today;t.gotoDate=gotoDate;t.incrementDate=incrementDate;t.zoomTo=zoomTo;t.getDate=getDate;t.getCalendar=getCalendar;t.getView=getView;t.option=option;t.trigger=trigger;var localeData=createObject(getMomentLocaleData(options.lang));if(options.monthNames){localeData._months=options.monthNames;}
if(options.monthNamesShort){localeData._monthsShort=options.monthNamesShort;}
if(options.dayNames){localeData._weekdays=options.dayNames;}
if(options.dayNamesShort){localeData._weekdaysShort=options.dayNamesShort;}
if(options.firstDay!=null){var _week=createObject(localeData._week);_week.dow=options.firstDay;localeData._week=_week;}
localeData._fullCalendar_weekCalc=(function(weekCalc){if(typeof weekCalc==='function'){return weekCalc;}
else if(weekCalc==='local'){return weekCalc;}
else if(weekCalc==='iso'||weekCalc==='ISO'){return'ISO';}})(options.weekNumberCalculation);t.defaultAllDayEventDuration=moment.duration(options.defaultAllDayEventDuration);t.defaultTimedEventDuration=moment.duration(options.defaultTimedEventDuration);t.moment=function(){var mom;if(options.timezone==='local'){mom=FC.moment.apply(null,arguments);if(mom.hasTime()){mom.local();}}
else if(options.timezone==='UTC'){mom=FC.moment.utc.apply(null,arguments);}
else{mom=FC.moment.parseZone.apply(null,arguments);}
if('_locale'in mom){mom._locale=localeData;}
else{mom._lang=localeData;}
return mom;};t.getIsAmbigTimezone=function(){return options.timezone!=='local'&&options.timezone!=='UTC';};t.applyTimezone=function(date){if(!date.hasTime()){return date.clone();}
var zonedDate=t.moment(date.toArray());var timeAdjust=date.time()-zonedDate.time();var adjustedZonedDate;if(timeAdjust){adjustedZonedDate=zonedDate.clone().add(timeAdjust);if(date.time()-adjustedZonedDate.time()===0){zonedDate=adjustedZonedDate;}}
return zonedDate;};t.getNow=function(){var now=options.now;if(typeof now==='function'){now=now();}
return t.moment(now).stripZone();};t.getEventEnd=function(event){if(event.end){return event.end.clone();}
else{return t.getDefaultEventEnd(event.allDay,event.start);}};t.getDefaultEventEnd=function(allDay,zonedStart){var end=zonedStart.clone();if(allDay){end.stripTime().add(t.defaultAllDayEventDuration);}
else{end.add(t.defaultTimedEventDuration);}
if(t.getIsAmbigTimezone()){end.stripZone();}
return end;};t.humanizeDuration=function(duration){return(duration.locale||duration.lang).call(duration,options.lang).humanize();};EventManager.call(t,options);var isFetchNeeded=t.isFetchNeeded;var fetchEvents=t.fetchEvents;var fetchEventSources=t.fetchEventSources;var _element=element[0];var header;var headerElement;var content;var tm;var currentView;var viewsByType={};var suggestedViewHeight;var windowResizeProxy;var ignoreWindowResize=0;var events=[];var date;if(options.defaultDate!=null){date=t.moment(options.defaultDate).stripZone();}
else{date=t.getNow();}
function render(){if(!content){initialRender();}
else if(elementVisible()){calcSize();renderView();}}
function initialRender(){tm=options.theme?'ui':'fc';element.addClass('fc');if(options.isRTL){element.addClass('fc-rtl');}
else{element.addClass('fc-ltr');}
if(options.theme){element.addClass('ui-widget');}
else{element.addClass('fc-unthemed');}
content=$("<div class='fc-view-container'/>").prependTo(element);header=t.header=new Header(t,options);headerElement=header.render();if(headerElement){element.prepend(headerElement);}
renderView(options.defaultView);if(options.handleWindowResize){windowResizeProxy=debounce(windowResize,options.windowResizeDelay);$(window).resize(windowResizeProxy);}}
function destroy(){if(currentView){currentView.removeElement();}
header.removeElement();content.remove();element.removeClass('fc fc-ltr fc-rtl fc-unthemed ui-widget');if(windowResizeProxy){$(window).unbind('resize',windowResizeProxy);}}
function elementVisible(){return element.is(':visible');}
function renderView(viewType){ignoreWindowResize++;if(currentView&&viewType&&currentView.type!==viewType){header.deactivateButton(currentView.type);freezeContentHeight();currentView.removeElement();currentView=t.view=null;}
if(!currentView&&viewType){currentView=t.view=viewsByType[viewType]||(viewsByType[viewType]=t.instantiateView(viewType));currentView.setElement($("<div class='fc-view fc-"+viewType+"-view' />").appendTo(content));header.activateButton(viewType);}
if(currentView){date=currentView.massageCurrentDate(date);if(!currentView.displaying||!date.isWithin(currentView.intervalStart,currentView.intervalEnd)){if(elementVisible()){currentView.display(date);unfreezeContentHeight();updateHeaderTitle();updateTodayButton();getAndRenderEvents();}}}
unfreezeContentHeight();ignoreWindowResize--;}
t.getSuggestedViewHeight=function(){if(suggestedViewHeight===undefined){calcSize();}
return suggestedViewHeight;};t.isHeightAuto=function(){return options.contentHeight==='auto'||options.height==='auto';};function updateSize(shouldRecalc){if(elementVisible()){if(shouldRecalc){_calcSize();}
ignoreWindowResize++;currentView.updateSize(true);ignoreWindowResize--;return true;}}
function calcSize(){if(elementVisible()){_calcSize();}}
function _calcSize(){if(typeof options.contentHeight==='number'){suggestedViewHeight=options.contentHeight;}
else if(typeof options.height==='number'){suggestedViewHeight=options.height-(headerElement?headerElement.outerHeight(true):0);}
else{suggestedViewHeight=Math.round(content.width()/Math.max(options.aspectRatio,.5));}}
function windowResize(ev){if(!ignoreWindowResize&&ev.target===window&&currentView.start){if(updateSize(true)){currentView.trigger('windowResize',_element);}}}
function refetchEvents(){fetchAndRenderEvents();}
function refetchEventSources(matchInputs){fetchEventSources(t.getEventSourcesByMatchArray(matchInputs));}
function renderEvents(){if(elementVisible()){freezeContentHeight();currentView.displayEvents(events);unfreezeContentHeight();}}
function getAndRenderEvents(){if(!options.lazyFetching||isFetchNeeded(currentView.start,currentView.end)){fetchAndRenderEvents();}
else{renderEvents();}}
function fetchAndRenderEvents(){fetchEvents(currentView.start,currentView.end);}
function reportEvents(_events){events=_events;renderEvents();}
function reportEventChange(){renderEvents();}
function updateHeaderTitle(){header.updateTitle(currentView.title);}
function updateTodayButton(){var now=t.getNow();if(now.isWithin(currentView.intervalStart,currentView.intervalEnd)){header.disableButton('today');}
else{header.enableButton('today');}}
function select(zonedStartInput,zonedEndInput){currentView.select(t.buildSelectSpan.apply(t,arguments));}
function unselect(){if(currentView){currentView.unselect();}}
function prev(){date=currentView.computePrevDate(date);renderView();}
function next(){date=currentView.computeNextDate(date);renderView();}
function prevYear(){date.add(-1,'years');renderView();}
function nextYear(){date.add(1,'years');renderView();}
function today(){date=t.getNow();renderView();}
function gotoDate(zonedDateInput){date=t.moment(zonedDateInput).stripZone();renderView();}
function incrementDate(delta){date.add(moment.duration(delta));renderView();}
function zoomTo(newDate,viewType){var spec;viewType=viewType||'day';spec=t.getViewSpec(viewType)||t.getUnitViewSpec(viewType);date=newDate.clone();renderView(spec?spec.type:null);}
function getDate(){return t.applyTimezone(date);}
t.freezeContentHeight=freezeContentHeight;t.unfreezeContentHeight=unfreezeContentHeight;function freezeContentHeight(){content.css({width:'100%',height:content.height(),overflow:'hidden'});}
function unfreezeContentHeight(){content.css({width:'',height:'',overflow:''});}
function getCalendar(){return t;}
function getView(){return currentView;}
function option(name,value){if(value===undefined){return options[name];}
if(name=='height'||name=='contentHeight'||name=='aspectRatio'){options[name]=value;updateSize(true);}}
function trigger(name,thisObj){var args=Array.prototype.slice.call(arguments,2);thisObj=thisObj||_element;this.triggerWith(name,thisObj,args);if(options[name]){return options[name].apply(thisObj,args);}}
t.initialize();};;Calendar.defaults={titleRangeSeparator:' \u2013 ',monthYearFormat:'MMMM YYYY',defaultTimedEventDuration:'02:00:00',defaultAllDayEventDuration:{days:1},forceEventDuration:false,nextDayThreshold:'09:00:00',defaultView:'month',aspectRatio:1.35,header:{left:'title',center:'',right:'today prev,next'},weekends:true,weekNumbers:false,weekNumberTitle:'W',weekNumberCalculation:'local',scrollTime:'06:00:00',lazyFetching:true,startParam:'start',endParam:'end',timezoneParam:'timezone',timezone:false,isRTL:false,buttonText:{prev:"prev",next:"next",prevYear:"prev year",nextYear:"next year",year:'year',today:'today',month:'month',week:'week',day:'day'},buttonIcons:{prev:'left-single-arrow',next:'right-single-arrow',prevYear:'left-double-arrow',nextYear:'right-double-arrow'},theme:false,themeButtonIcons:{prev:'circle-triangle-w',next:'circle-triangle-e',prevYear:'seek-prev',nextYear:'seek-next'},dragOpacity:.75,dragRevertDuration:500,dragScroll:true,unselectAuto:true,dropAccept:'*',eventOrder:'title',eventLimit:false,eventLimitText:'more',eventLimitClick:'popover',dayPopoverFormat:'LL',handleWindowResize:true,windowResizeDelay:200,longPressDelay:1000};Calendar.englishDefaults={dayPopoverFormat:'dddd, MMMM D'};Calendar.rtlDefaults={header:{left:'next,prev today',center:'',right:'title'},buttonIcons:{prev:'right-single-arrow',next:'left-single-arrow',prevYear:'right-double-arrow',nextYear:'left-double-arrow'},themeButtonIcons:{prev:'circle-triangle-e',next:'circle-triangle-w',nextYear:'seek-prev',prevYear:'seek-next'}};;;var langOptionHash=FC.langs={};FC.datepickerLang=function(langCode,dpLangCode,dpOptions){var fcOptions=langOptionHash[langCode]||(langOptionHash[langCode]={});fcOptions.isRTL=dpOptions.isRTL;fcOptions.weekNumberTitle=dpOptions.weekHeader;$.each(dpComputableOptions,function(name,func){fcOptions[name]=func(dpOptions);});if($.datepicker){$.datepicker.regional[dpLangCode]=$.datepicker.regional[langCode]=dpOptions;$.datepicker.regional.en=$.datepicker.regional[''];$.datepicker.setDefaults(dpOptions);}};FC.lang=function(langCode,newFcOptions){var fcOptions;var momOptions;fcOptions=langOptionHash[langCode]||(langOptionHash[langCode]={});if(newFcOptions){fcOptions=langOptionHash[langCode]=mergeOptions([fcOptions,newFcOptions]);}
momOptions=getMomentLocaleData(langCode);$.each(momComputableOptions,function(name,func){if(fcOptions[name]==null){fcOptions[name]=func(momOptions,fcOptions);}});Calendar.defaults.lang=langCode;};var dpComputableOptions={buttonText:function(dpOptions){return{prev:stripHtmlEntities(dpOptions.prevText),next:stripHtmlEntities(dpOptions.nextText),today:stripHtmlEntities(dpOptions.currentText)};},monthYearFormat:function(dpOptions){return dpOptions.showMonthAfterYear?'YYYY['+dpOptions.yearSuffix+'] MMMM':'MMMM YYYY['+dpOptions.yearSuffix+']';}};var momComputableOptions={dayOfMonthFormat:function(momOptions,fcOptions){var format=momOptions.longDateFormat('l');format=format.replace(/^Y+[^\w\s]*|[^\w\s]*Y+$/g,'');if(fcOptions.isRTL){format+=' ddd';}
else{format='ddd '+format;}
return format;},mediumTimeFormat:function(momOptions){return momOptions.longDateFormat('LT').replace(/\s*a$/i,'a');},smallTimeFormat:function(momOptions){return momOptions.longDateFormat('LT').replace(':mm','(:mm)').replace(/(\Wmm)$/,'($1)').replace(/\s*a$/i,'a');},extraSmallTimeFormat:function(momOptions){return momOptions.longDateFormat('LT').replace(':mm','(:mm)').replace(/(\Wmm)$/,'($1)').replace(/\s*a$/i,'t');},hourFormat:function(momOptions){return momOptions.longDateFormat('LT').replace(':mm','').replace(/(\Wmm)$/,'').replace(/\s*a$/i,'a');},noMeridiemTimeFormat:function(momOptions){return momOptions.longDateFormat('LT').replace(/\s*a$/i,'');}};var instanceComputableOptions={smallDayDateFormat:function(options){return options.isRTL?'D dd':'dd D';},weekFormat:function(options){return options.isRTL?'w[ '+options.weekNumberTitle+']':'['+options.weekNumberTitle+' ]w';},smallWeekFormat:function(options){return options.isRTL?'w['+options.weekNumberTitle+']':'['+options.weekNumberTitle+']w';}};function populateInstanceComputableOptions(options){$.each(instanceComputableOptions,function(name,func){if(options[name]==null){options[name]=func(options);}});}
function getMomentLocaleData(langCode){var func=moment.localeData||moment.langData;return func.call(moment,langCode)||func.call(moment,'en');}
FC.lang('en',Calendar.englishDefaults);;;function Header(calendar,options){var t=this;t.render=render;t.removeElement=removeElement;t.updateTitle=updateTitle;t.activateButton=activateButton;t.deactivateButton=deactivateButton;t.disableButton=disableButton;t.enableButton=enableButton;t.getViewsWithButtons=getViewsWithButtons;var el=$();var viewsWithButtons=[];var tm;function render(){var sections=options.header;tm=options.theme?'ui':'fc';if(sections){el=$("<div class='fc-toolbar'/>").append(renderSection('left')).append(renderSection('right')).append(renderSection('center')).append('<div class="fc-clear"/>');return el;}}
function removeElement(){el.remove();el=$();}
function renderSection(position){var sectionEl=$('<div class="fc-'+position+'"/>');var buttonStr=options.header[position];if(buttonStr){$.each(buttonStr.split(' '),function(i){var groupChildren=$();var isOnlyButtons=true;var groupEl;$.each(this.split(','),function(j,buttonName){var customButtonProps;var viewSpec;var buttonClick;var overrideText;var defaultText;var themeIcon;var normalIcon;var innerHtml;var classes;var button;if(buttonName=='title'){groupChildren=groupChildren.add($('<h2>&nbsp;</h2>'));isOnlyButtons=false;}
else{if((customButtonProps=(calendar.options.customButtons||{})[buttonName])){buttonClick=function(ev){if(customButtonProps.click){customButtonProps.click.call(button[0],ev);}};overrideText='';defaultText=customButtonProps.text;}
else if((viewSpec=calendar.getViewSpec(buttonName))){buttonClick=function(){calendar.changeView(buttonName);};viewsWithButtons.push(buttonName);overrideText=viewSpec.buttonTextOverride;defaultText=viewSpec.buttonTextDefault;}
else if(calendar[buttonName]){buttonClick=function(){calendar[buttonName]();};overrideText=(calendar.overrides.buttonText||{})[buttonName];defaultText=options.buttonText[buttonName];}
if(buttonClick){themeIcon=customButtonProps?customButtonProps.themeIcon:options.themeButtonIcons[buttonName];normalIcon=customButtonProps?customButtonProps.icon:options.buttonIcons[buttonName];if(overrideText){innerHtml=htmlEscape(overrideText);}
else if(themeIcon&&options.theme){innerHtml="<span class='ui-icon ui-icon-"+themeIcon+"'></span>";}
else if(normalIcon&&!options.theme){innerHtml="<span class='fc-icon fc-icon-"+normalIcon+"'></span>";}
else{innerHtml=htmlEscape(defaultText);}
classes=['fc-'+buttonName+'-button',tm+'-button',tm+'-state-default'];button=$('<button type="button" class="'+classes.join(' ')+'">'+
innerHtml+'</button>').click(function(ev){if(!button.hasClass(tm+'-state-disabled')){buttonClick(ev);if(button.hasClass(tm+'-state-active')||button.hasClass(tm+'-state-disabled')){button.removeClass(tm+'-state-hover');}}}).mousedown(function(){button.not('.'+tm+'-state-active').not('.'+tm+'-state-disabled').addClass(tm+'-state-down');}).mouseup(function(){button.removeClass(tm+'-state-down');}).hover(function(){button.not('.'+tm+'-state-active').not('.'+tm+'-state-disabled').addClass(tm+'-state-hover');},function(){button.removeClass(tm+'-state-hover').removeClass(tm+'-state-down');});groupChildren=groupChildren.add(button);}}});if(isOnlyButtons){groupChildren.first().addClass(tm+'-corner-left').end().last().addClass(tm+'-corner-right').end();}
if(groupChildren.length>1){groupEl=$('<div/>');if(isOnlyButtons){groupEl.addClass('fc-button-group');}
groupEl.append(groupChildren);sectionEl.append(groupEl);}
else{sectionEl.append(groupChildren);}});}
return sectionEl;}
function updateTitle(text){el.find('h2').text(text);}
function activateButton(buttonName){el.find('.fc-'+buttonName+'-button').addClass(tm+'-state-active');}
function deactivateButton(buttonName){el.find('.fc-'+buttonName+'-button').removeClass(tm+'-state-active');}
function disableButton(buttonName){el.find('.fc-'+buttonName+'-button').prop('disabled',true).addClass(tm+'-state-disabled');}
function enableButton(buttonName){el.find('.fc-'+buttonName+'-button').prop('disabled',false).removeClass(tm+'-state-disabled');}
function getViewsWithButtons(){return viewsWithButtons;}};;FC.sourceNormalizers=[];FC.sourceFetchers=[];var ajaxDefaults={dataType:'json',cache:false};var eventGUID=1;function EventManager(options){var t=this;t.isFetchNeeded=isFetchNeeded;t.fetchEvents=fetchEvents;t.fetchEventSources=fetchEventSources;t.getEventSources=getEventSources;t.getEventSourceById=getEventSourceById;t.getEventSourcesByMatchArray=getEventSourcesByMatchArray;t.getEventSourcesByMatch=getEventSourcesByMatch;t.addEventSource=addEventSource;t.removeEventSource=removeEventSource;t.removeEventSources=removeEventSources;t.updateEvent=updateEvent;t.renderEvent=renderEvent;t.removeEvents=removeEvents;t.clientEvents=clientEvents;t.mutateEvent=mutateEvent;t.normalizeEventDates=normalizeEventDates;t.normalizeEventTimes=normalizeEventTimes;var reportEvents=t.reportEvents;var stickySource={events:[]};var sources=[stickySource];var rangeStart,rangeEnd;var pendingSourceCnt=0;var cache=[];$.each((options.events?[options.events]:[]).concat(options.eventSources||[]),function(i,sourceInput){var source=buildEventSource(sourceInput);if(source){sources.push(source);}});function isFetchNeeded(start,end){return!rangeStart||start<rangeStart||end>rangeEnd;}
function fetchEvents(start,end){rangeStart=start;rangeEnd=end;fetchEventSources(sources,'reset');}
function fetchEventSources(specificSources,specialFetchType){var i,source;if(specialFetchType==='reset'){cache=[];}
else if(specialFetchType!=='add'){cache=excludeEventsBySources(cache,specificSources);}
for(i=0;i<specificSources.length;i++){source=specificSources[i];if(source._status!=='pending'){pendingSourceCnt++;}
source._fetchId=(source._fetchId||0)+1;source._status='pending';}
for(i=0;i<specificSources.length;i++){source=specificSources[i];tryFetchEventSource(source,source._fetchId);}}
function tryFetchEventSource(source,fetchId){_fetchEventSource(source,function(eventInputs){var isArraySource=$.isArray(source.events);var i,eventInput;var abstractEvent;if(fetchId===source._fetchId&&source._status!=='rejected'){source._status='resolved';if(eventInputs){for(i=0;i<eventInputs.length;i++){eventInput=eventInputs[i];if(isArraySource){abstractEvent=eventInput;}
else{abstractEvent=buildEventFromInput(eventInput,source);}
if(abstractEvent){cache.push.apply(cache,expandEvent(abstractEvent));}}}
decrementPendingSourceCnt();}});}
function rejectEventSource(source){var wasPending=source._status==='pending';source._status='rejected';if(wasPending){decrementPendingSourceCnt();}}
function decrementPendingSourceCnt(){pendingSourceCnt--;if(!pendingSourceCnt){reportEvents(cache);}}
function _fetchEventSource(source,callback){var i;var fetchers=FC.sourceFetchers;var res;for(i=0;i<fetchers.length;i++){res=fetchers[i].call(t,source,rangeStart.clone(),rangeEnd.clone(),options.timezone,callback);if(res===true){return;}
else if(typeof res=='object'){_fetchEventSource(res,callback);return;}}
var events=source.events;if(events){if($.isFunction(events)){t.pushLoading();events.call(t,rangeStart.clone(),rangeEnd.clone(),options.timezone,function(events){callback(events);t.popLoading();});}
else if($.isArray(events)){callback(events);}
else{callback();}}else{var url=source.url;if(url){var success=source.success;var error=source.error;var complete=source.complete;var customData;if($.isFunction(source.data)){customData=source.data();}
else{customData=source.data;}
var data=$.extend({},customData||{});var startParam=firstDefined(source.startParam,options.startParam);var endParam=firstDefined(source.endParam,options.endParam);var timezoneParam=firstDefined(source.timezoneParam,options.timezoneParam);if(startParam){data[startParam]=rangeStart.format();}
if(endParam){data[endParam]=rangeEnd.format();}
if(options.timezone&&options.timezone!='local'){data[timezoneParam]=options.timezone;}
t.pushLoading();$.ajax($.extend({},ajaxDefaults,source,{data:data,success:function(events){events=events||[];var res=applyAll(success,this,arguments);if($.isArray(res)){events=res;}
callback(events);},error:function(){applyAll(error,this,arguments);callback();},complete:function(){applyAll(complete,this,arguments);t.popLoading();}}));}else{callback();}}}
function addEventSource(sourceInput){var source=buildEventSource(sourceInput);if(source){sources.push(source);fetchEventSources([source],'add');}}
function buildEventSource(sourceInput){var normalizers=FC.sourceNormalizers;var source;var i;if($.isFunction(sourceInput)||$.isArray(sourceInput)){source={events:sourceInput};}
else if(typeof sourceInput==='string'){source={url:sourceInput};}
else if(typeof sourceInput==='object'){source=$.extend({},sourceInput);}
if(source){if(source.className){if(typeof source.className==='string'){source.className=source.className.split(/\s+/);}}
else{source.className=[];}
if($.isArray(source.events)){source.origArray=source.events;source.events=$.map(source.events,function(eventInput){return buildEventFromInput(eventInput,source);});}
for(i=0;i<normalizers.length;i++){normalizers[i].call(t,source);}
return source;}}
function removeEventSource(matchInput){removeSpecificEventSources(getEventSourcesByMatch(matchInput));}
function removeEventSources(matchInputs){if(matchInputs==null){removeSpecificEventSources(sources,true);}
else{removeSpecificEventSources(getEventSourcesByMatchArray(matchInputs));}}
function removeSpecificEventSources(targetSources,isAll){var i;for(i=0;i<targetSources.length;i++){rejectEventSource(targetSources[i]);}
if(isAll){sources=[];cache=[];}
else{sources=$.grep(sources,function(source){for(i=0;i<targetSources.length;i++){if(source===targetSources[i]){return false;}}
return true;});cache=excludeEventsBySources(cache,targetSources);}
reportEvents(cache);}
function getEventSources(){return sources.slice(1);}
function getEventSourceById(id){return $.grep(sources,function(source){return source.id&&source.id===id;})[0];}
function getEventSourcesByMatchArray(matchInputs){if(!matchInputs){matchInputs=[];}
else if(!$.isArray(matchInputs)){matchInputs=[matchInputs];}
var matchingSources=[];var i;for(i=0;i<matchInputs.length;i++){matchingSources.push.apply(matchingSources,getEventSourcesByMatch(matchInputs[i]));}
return matchingSources;}
function getEventSourcesByMatch(matchInput){var i,source;for(i=0;i<sources.length;i++){source=sources[i];if(source===matchInput){return[source];}}
source=getEventSourceById(matchInput);if(source){return[source];}
return $.grep(sources,function(source){return isSourcesEquivalent(matchInput,source);});}
function isSourcesEquivalent(source1,source2){return source1&&source2&&getSourcePrimitive(source1)==getSourcePrimitive(source2);}
function getSourcePrimitive(source){return((typeof source==='object')?(source.origArray||source.googleCalendarId||source.url||source.events):null)||source;}
function excludeEventsBySources(specificEvents,specificSources){return $.grep(specificEvents,function(event){for(var i=0;i<specificSources.length;i++){if(event.source===specificSources[i]){return false;}}
return true;});}
function updateEvent(event){event.start=t.moment(event.start);if(event.end){event.end=t.moment(event.end);}
else{event.end=null;}
mutateEvent(event,getMiscEventProps(event));reportEvents(cache);}
function getMiscEventProps(event){var props={};$.each(event,function(name,val){if(isMiscEventPropName(name)){if(val!==undefined&&isAtomic(val)){props[name]=val;}}});return props;}
function isMiscEventPropName(name){return!/^_|^(id|allDay|start|end)$/.test(name);}
function renderEvent(eventInput,stick){var abstractEvent=buildEventFromInput(eventInput);var events;var i,event;if(abstractEvent){events=expandEvent(abstractEvent);for(i=0;i<events.length;i++){event=events[i];if(!event.source){if(stick){stickySource.events.push(event);event.source=stickySource;}
cache.push(event);}}
reportEvents(cache);return events;}
return[];}
function removeEvents(filter){var eventID;var i;if(filter==null){filter=function(){return true;};}
else if(!$.isFunction(filter)){eventID=filter+'';filter=function(event){return event._id==eventID;};}
cache=$.grep(cache,filter,true);for(i=0;i<sources.length;i++){if($.isArray(sources[i].events)){sources[i].events=$.grep(sources[i].events,filter,true);}}
reportEvents(cache);}
function clientEvents(filter){if($.isFunction(filter)){return $.grep(cache,filter);}
else if(filter!=null){filter+='';return $.grep(cache,function(e){return e._id==filter;});}
return cache;}
function buildEventFromInput(input,source){var out={};var start,end;var allDay;if(options.eventDataTransform){input=options.eventDataTransform(input);}
if(source&&source.eventDataTransform){input=source.eventDataTransform(input);}
$.extend(out,input);if(source){out.source=source;}
out._id=input._id||(input.id===undefined?'_fc'+eventGUID++:input.id+'');if(input.className){if(typeof input.className=='string'){out.className=input.className.split(/\s+/);}
else{out.className=input.className;}}
else{out.className=[];}
start=input.start||input.date;end=input.end;if(isTimeString(start)){start=moment.duration(start);}
if(isTimeString(end)){end=moment.duration(end);}
if(input.dow||moment.isDuration(start)||moment.isDuration(end)){out.start=start?moment.duration(start):null;out.end=end?moment.duration(end):null;out._recurring=true;}
else{if(start){start=t.moment(start);if(!start.isValid()){return false;}}
if(end){end=t.moment(end);if(!end.isValid()){end=null;}}
allDay=input.allDay;if(allDay===undefined){allDay=firstDefined(source?source.allDayDefault:undefined,options.allDayDefault);}
assignDatesToEvent(start,end,allDay,out);}
t.normalizeEvent(out);return out;}
function assignDatesToEvent(start,end,allDay,event){event.start=start;event.end=end;event.allDay=allDay;normalizeEventDates(event);backupEventDates(event);}
function normalizeEventDates(eventProps){normalizeEventTimes(eventProps);if(eventProps.end&&!eventProps.end.isAfter(eventProps.start)){eventProps.end=null;}
if(!eventProps.end){if(options.forceEventDuration){eventProps.end=t.getDefaultEventEnd(eventProps.allDay,eventProps.start);}
else{eventProps.end=null;}}}
function normalizeEventTimes(eventProps){if(eventProps.allDay==null){eventProps.allDay=!(eventProps.start.hasTime()||(eventProps.end&&eventProps.end.hasTime()));}
if(eventProps.allDay){eventProps.start.stripTime();if(eventProps.end){eventProps.end.stripTime();}}
else{if(!eventProps.start.hasTime()){eventProps.start=t.applyTimezone(eventProps.start.time(0));}
if(eventProps.end&&!eventProps.end.hasTime()){eventProps.end=t.applyTimezone(eventProps.end.time(0));}}}
function expandEvent(abstractEvent,_rangeStart,_rangeEnd){var events=[];var dowHash;var dow;var i;var date;var startTime,endTime;var start,end;var event;_rangeStart=_rangeStart||rangeStart;_rangeEnd=_rangeEnd||rangeEnd;if(abstractEvent){if(abstractEvent._recurring){if((dow=abstractEvent.dow)){dowHash={};for(i=0;i<dow.length;i++){dowHash[dow[i]]=true;}}
date=_rangeStart.clone().stripTime();while(date.isBefore(_rangeEnd)){if(!dowHash||dowHash[date.day()]){startTime=abstractEvent.start;endTime=abstractEvent.end;start=date.clone();end=null;if(startTime){start=start.time(startTime);}
if(endTime){end=date.clone().time(endTime);}
event=$.extend({},abstractEvent);assignDatesToEvent(start,end,!startTime&&!endTime,event);events.push(event);}
date.add(1,'days');}}
else{events.push(abstractEvent);}}
return events;}
function mutateEvent(event,newProps,largeUnit){var miscProps={};var oldProps;var clearEnd;var startDelta;var endDelta;var durationDelta;var undoFunc;function diffDates(date1,date0){if(largeUnit){return diffByUnit(date1,date0,largeUnit);}
else if(newProps.allDay){return diffDay(date1,date0);}
else{return diffDayTime(date1,date0);}}
newProps=newProps||{};if(!newProps.start){newProps.start=event.start.clone();}
if(newProps.end===undefined){newProps.end=event.end?event.end.clone():null;}
if(newProps.allDay==null){newProps.allDay=event.allDay;}
normalizeEventDates(newProps);oldProps={start:event._start.clone(),end:event._end?event._end.clone():t.getDefaultEventEnd(event._allDay,event._start),allDay:newProps.allDay};normalizeEventDates(oldProps);clearEnd=event._end!==null&&newProps.end===null;startDelta=diffDates(newProps.start,oldProps.start);if(newProps.end){endDelta=diffDates(newProps.end,oldProps.end);durationDelta=endDelta.subtract(startDelta);}
else{durationDelta=null;}
$.each(newProps,function(name,val){if(isMiscEventPropName(name)){if(val!==undefined){miscProps[name]=val;}}});undoFunc=mutateEvents(clientEvents(event._id),clearEnd,newProps.allDay,startDelta,durationDelta,miscProps);return{dateDelta:startDelta,durationDelta:durationDelta,undo:undoFunc};}
function mutateEvents(events,clearEnd,allDay,dateDelta,durationDelta,miscProps){var isAmbigTimezone=t.getIsAmbigTimezone();var undoFunctions=[];if(dateDelta&&!dateDelta.valueOf()){dateDelta=null;}
if(durationDelta&&!durationDelta.valueOf()){durationDelta=null;}
$.each(events,function(i,event){var oldProps;var newProps;oldProps={start:event.start.clone(),end:event.end?event.end.clone():null,allDay:event.allDay};$.each(miscProps,function(name){oldProps[name]=event[name];});newProps={start:event._start,end:event._end,allDay:allDay};normalizeEventDates(newProps);if(clearEnd){newProps.end=null;}
else if(durationDelta&&!newProps.end){newProps.end=t.getDefaultEventEnd(newProps.allDay,newProps.start);}
if(dateDelta){newProps.start.add(dateDelta);if(newProps.end){newProps.end.add(dateDelta);}}
if(durationDelta){newProps.end.add(durationDelta);}
if(isAmbigTimezone&&!newProps.allDay&&(dateDelta||durationDelta)){newProps.start.stripZone();if(newProps.end){newProps.end.stripZone();}}
$.extend(event,miscProps,newProps);backupEventDates(event);undoFunctions.push(function(){$.extend(event,oldProps);backupEventDates(event);});});return function(){for(var i=0;i<undoFunctions.length;i++){undoFunctions[i]();}};}
t.getBusinessHoursEvents=getBusinessHoursEvents;function getBusinessHoursEvents(wholeDay){var optionVal=options.businessHours;var defaultVal={className:'fc-nonbusiness',start:'09:00',end:'17:00',dow:[1,2,3,4,5],rendering:'inverse-background'};var view=t.getView();var eventInput;if(optionVal){eventInput=$.extend({},defaultVal,typeof optionVal==='object'?optionVal:{});}
if(eventInput){if(wholeDay){eventInput.start=null;eventInput.end=null;}
return expandEvent(buildEventFromInput(eventInput),view.start,view.end);}
return[];}
t.isEventSpanAllowed=isEventSpanAllowed;t.isExternalSpanAllowed=isExternalSpanAllowed;t.isSelectionSpanAllowed=isSelectionSpanAllowed;function isEventSpanAllowed(span,event){var source=event.source||{};var constraint=firstDefined(event.constraint,source.constraint,options.eventConstraint);var overlap=firstDefined(event.overlap,source.overlap,options.eventOverlap);return isSpanAllowed(span,constraint,overlap,event);}
function isExternalSpanAllowed(eventSpan,eventLocation,eventProps){var eventInput;var event;if(eventProps){eventInput=$.extend({},eventProps,eventLocation);event=expandEvent(buildEventFromInput(eventInput))[0];}
if(event){return isEventSpanAllowed(eventSpan,event);}
else{return isSelectionSpanAllowed(eventSpan);}}
function isSelectionSpanAllowed(span){return isSpanAllowed(span,options.selectConstraint,options.selectOverlap);}
function isSpanAllowed(span,constraint,overlap,event){var constraintEvents;var anyContainment;var peerEvents;var i,peerEvent;var peerOverlap;if(constraint!=null){constraintEvents=constraintToEvents(constraint);anyContainment=false;for(i=0;i<constraintEvents.length;i++){if(eventContainsRange(constraintEvents[i],span)){anyContainment=true;break;}}
if(!anyContainment){return false;}}
peerEvents=t.getPeerEvents(span,event);for(i=0;i<peerEvents.length;i++){peerEvent=peerEvents[i];if(eventIntersectsRange(peerEvent,span)){if(overlap===false){return false;}
else if(typeof overlap==='function'&&!overlap(peerEvent,event)){return false;}
if(event){peerOverlap=firstDefined(peerEvent.overlap,(peerEvent.source||{}).overlap);if(peerOverlap===false){return false;}
if(typeof peerOverlap==='function'&&!peerOverlap(event,peerEvent)){return false;}}}}
return true;}
function constraintToEvents(constraintInput){if(constraintInput==='businessHours'){return getBusinessHoursEvents();}
if(typeof constraintInput==='object'){return expandEvent(buildEventFromInput(constraintInput));}
return clientEvents(constraintInput);}
function eventContainsRange(event,range){var eventStart=event.start.clone().stripZone();var eventEnd=t.getEventEnd(event).stripZone();return range.start>=eventStart&&range.end<=eventEnd;}
function eventIntersectsRange(event,range){var eventStart=event.start.clone().stripZone();var eventEnd=t.getEventEnd(event).stripZone();return range.start<eventEnd&&range.end>eventStart;}
t.getEventCache=function(){return cache;};}
Calendar.prototype.normalizeEvent=function(event){};Calendar.prototype.getPeerEvents=function(span,event){var cache=this.getEventCache();var peerEvents=[];var i,otherEvent;for(i=0;i<cache.length;i++){otherEvent=cache[i];if(!event||event._id!==otherEvent._id){peerEvents.push(otherEvent);}}
return peerEvents;};function backupEventDates(event){event._allDay=event.allDay;event._start=event.start.clone();event._end=event.end?event.end.clone():null;};;var BasicView=FC.BasicView=View.extend({scroller:null,dayGridClass:DayGrid,dayGrid:null,dayNumbersVisible:false,weekNumbersVisible:false,weekNumberWidth:null,headContainerEl:null,headRowEl:null,initialize:function(){this.dayGrid=this.instantiateDayGrid();this.scroller=new Scroller({overflowX:'hidden',overflowY:'auto'});},instantiateDayGrid:function(){var subclass=this.dayGridClass.extend(basicDayGridMethods);return new subclass(this);},setRange:function(range){View.prototype.setRange.call(this,range);this.dayGrid.breakOnWeeks=/year|month|week/.test(this.intervalUnit);this.dayGrid.setRange(range);},computeRange:function(date){var range=View.prototype.computeRange.call(this,date);if(/year|month/.test(range.intervalUnit)){range.start.startOf('week');range.start=this.skipHiddenDays(range.start);if(range.end.weekday()){range.end.add(1,'week').startOf('week');range.end=this.skipHiddenDays(range.end,-1,true);}}
return range;},renderDates:function(){this.dayNumbersVisible=this.dayGrid.rowCnt>1;this.weekNumbersVisible=this.opt('weekNumbers');this.dayGrid.numbersVisible=this.dayNumbersVisible||this.weekNumbersVisible;this.el.addClass('fc-basic-view').html(this.renderSkeletonHtml());this.renderHead();this.scroller.render();var dayGridContainerEl=this.scroller.el.addClass('fc-day-grid-container');var dayGridEl=$('<div class="fc-day-grid" />').appendTo(dayGridContainerEl);this.el.find('.fc-body > tr > td').append(dayGridContainerEl);this.dayGrid.setElement(dayGridEl);this.dayGrid.renderDates(this.hasRigidRows());},renderHead:function(){this.headContainerEl=this.el.find('.fc-head-container').html(this.dayGrid.renderHeadHtml());this.headRowEl=this.headContainerEl.find('.fc-row');},unrenderDates:function(){this.dayGrid.unrenderDates();this.dayGrid.removeElement();this.scroller.destroy();},renderBusinessHours:function(){this.dayGrid.renderBusinessHours();},renderSkeletonHtml:function(){return''+'<table>'+'<thead class="fc-head">'+'<tr>'+'<td class="fc-head-container '+this.widgetHeaderClass+'"></td>'+'</tr>'+'</thead>'+'<tbody class="fc-body">'+'<tr>'+'<td class="'+this.widgetContentClass+'"></td>'+'</tr>'+'</tbody>'+'</table>';},weekNumberStyleAttr:function(){if(this.weekNumberWidth!==null){return'style="width:'+this.weekNumberWidth+'px"';}
return'';},hasRigidRows:function(){var eventLimit=this.opt('eventLimit');return eventLimit&&typeof eventLimit!=='number';},updateWidth:function(){if(this.weekNumbersVisible){this.weekNumberWidth=matchCellWidths(this.el.find('.fc-week-number'));}},setHeight:function(totalHeight,isAuto){var eventLimit=this.opt('eventLimit');var scrollerHeight;var scrollbarWidths;this.scroller.clear();uncompensateScroll(this.headRowEl);this.dayGrid.removeSegPopover();if(eventLimit&&typeof eventLimit==='number'){this.dayGrid.limitRows(eventLimit);}
scrollerHeight=this.computeScrollerHeight(totalHeight);this.setGridHeight(scrollerHeight,isAuto);if(eventLimit&&typeof eventLimit!=='number'){this.dayGrid.limitRows(eventLimit);}
if(!isAuto){this.scroller.setHeight(scrollerHeight);scrollbarWidths=this.scroller.getScrollbarWidths();if(scrollbarWidths.left||scrollbarWidths.right){compensateScroll(this.headRowEl,scrollbarWidths);scrollerHeight=this.computeScrollerHeight(totalHeight);this.scroller.setHeight(scrollerHeight);}
this.scroller.lockOverflow(scrollbarWidths);}},computeScrollerHeight:function(totalHeight){return totalHeight-
subtractInnerElHeight(this.el,this.scroller.el);},setGridHeight:function(height,isAuto){if(isAuto){undistributeHeight(this.dayGrid.rowEls);}
else{distributeHeight(this.dayGrid.rowEls,height,true);}},queryScroll:function(){return this.scroller.getScrollTop();},setScroll:function(top){this.scroller.setScrollTop(top);},prepareHits:function(){this.dayGrid.prepareHits();},releaseHits:function(){this.dayGrid.releaseHits();},queryHit:function(left,top){return this.dayGrid.queryHit(left,top);},getHitSpan:function(hit){return this.dayGrid.getHitSpan(hit);},getHitEl:function(hit){return this.dayGrid.getHitEl(hit);},renderEvents:function(events){this.dayGrid.renderEvents(events);this.updateHeight();},getEventSegs:function(){return this.dayGrid.getEventSegs();},unrenderEvents:function(){this.dayGrid.unrenderEvents();},renderDrag:function(dropLocation,seg){return this.dayGrid.renderDrag(dropLocation,seg);},unrenderDrag:function(){this.dayGrid.unrenderDrag();},renderSelection:function(span){this.dayGrid.renderSelection(span);},unrenderSelection:function(){this.dayGrid.unrenderSelection();}});var basicDayGridMethods={renderHeadIntroHtml:function(){var view=this.view;if(view.weekNumbersVisible){return''+'<th class="fc-week-number '+view.widgetHeaderClass+'" '+view.weekNumberStyleAttr()+'>'+'<span>'+
htmlEscape(view.opt('weekNumberTitle'))+'</span>'+'</th>';}
return'';},renderNumberIntroHtml:function(row){var view=this.view;if(view.weekNumbersVisible){return''+'<td class="fc-week-number" '+view.weekNumberStyleAttr()+'>'+'<span>'+
this.getCellDate(row,0).format('w')+'</span>'+'</td>';}
return'';},renderBgIntroHtml:function(){var view=this.view;if(view.weekNumbersVisible){return'<td class="fc-week-number '+view.widgetContentClass+'" '+
view.weekNumberStyleAttr()+'></td>';}
return'';},renderIntroHtml:function(){var view=this.view;if(view.weekNumbersVisible){return'<td class="fc-week-number" '+view.weekNumberStyleAttr()+'></td>';}
return'';}};;;var MonthView=FC.MonthView=BasicView.extend({computeRange:function(date){var range=BasicView.prototype.computeRange.call(this,date);var rowCnt;if(this.isFixedWeeks()){rowCnt=Math.ceil(range.end.diff(range.start,'weeks',true));range.end.add(6-rowCnt,'weeks');}
return range;},setGridHeight:function(height,isAuto){isAuto=isAuto||this.opt('weekMode')==='variable';if(isAuto){height*=this.rowCnt/6;}
distributeHeight(this.dayGrid.rowEls,height,!isAuto);},isFixedWeeks:function(){var weekMode=this.opt('weekMode');if(weekMode){return weekMode==='fixed';}
return this.opt('fixedWeekCount');}});;;fcViews.basic={'class':BasicView};fcViews.basicDay={type:'basic',duration:{days:1}};fcViews.basicWeek={type:'basic',duration:{weeks:1}};fcViews.month={'class':MonthView,duration:{months:1},defaults:{fixedWeekCount:true}};;;var AgendaView=FC.AgendaView=View.extend({scroller:null,timeGridClass:TimeGrid,timeGrid:null,dayGridClass:DayGrid,dayGrid:null,axisWidth:null,headContainerEl:null,noScrollRowEls:null,bottomRuleEl:null,initialize:function(){this.timeGrid=this.instantiateTimeGrid();if(this.opt('allDaySlot')){this.dayGrid=this.instantiateDayGrid();}
this.scroller=new Scroller({overflowX:'hidden',overflowY:'auto'});},instantiateTimeGrid:function(){var subclass=this.timeGridClass.extend(agendaTimeGridMethods);return new subclass(this);},instantiateDayGrid:function(){var subclass=this.dayGridClass.extend(agendaDayGridMethods);return new subclass(this);},setRange:function(range){View.prototype.setRange.call(this,range);this.timeGrid.setRange(range);if(this.dayGrid){this.dayGrid.setRange(range);}},renderDates:function(){this.el.addClass('fc-agenda-view').html(this.renderSkeletonHtml());this.renderHead();this.scroller.render();var timeGridWrapEl=this.scroller.el.addClass('fc-time-grid-container');var timeGridEl=$('<div class="fc-time-grid" />').appendTo(timeGridWrapEl);this.el.find('.fc-body > tr > td').append(timeGridWrapEl);this.timeGrid.setElement(timeGridEl);this.timeGrid.renderDates();this.bottomRuleEl=$('<hr class="fc-divider '+this.widgetHeaderClass+'"/>').appendTo(this.timeGrid.el);if(this.dayGrid){this.dayGrid.setElement(this.el.find('.fc-day-grid'));this.dayGrid.renderDates();this.dayGrid.bottomCoordPadding=this.dayGrid.el.next('hr').outerHeight();}
this.noScrollRowEls=this.el.find('.fc-row:not(.fc-scroller *)');},renderHead:function(){this.headContainerEl=this.el.find('.fc-head-container').html(this.timeGrid.renderHeadHtml());},unrenderDates:function(){this.timeGrid.unrenderDates();this.timeGrid.removeElement();if(this.dayGrid){this.dayGrid.unrenderDates();this.dayGrid.removeElement();}
this.scroller.destroy();},renderSkeletonHtml:function(){return''+'<table>'+'<thead class="fc-head">'+'<tr>'+'<td class="fc-head-container '+this.widgetHeaderClass+'"></td>'+'</tr>'+'</thead>'+'<tbody class="fc-body">'+'<tr>'+'<td class="'+this.widgetContentClass+'">'+
(this.dayGrid?'<div class="fc-day-grid"/>'+'<hr class="fc-divider '+this.widgetHeaderClass+'"/>':'')+'</td>'+'</tr>'+'</tbody>'+'</table>';},axisStyleAttr:function(){if(this.axisWidth!==null){return'style="width:'+this.axisWidth+'px"';}
return'';},renderBusinessHours:function(){this.timeGrid.renderBusinessHours();if(this.dayGrid){this.dayGrid.renderBusinessHours();}},unrenderBusinessHours:function(){this.timeGrid.unrenderBusinessHours();if(this.dayGrid){this.dayGrid.unrenderBusinessHours();}},getNowIndicatorUnit:function(){return this.timeGrid.getNowIndicatorUnit();},renderNowIndicator:function(date){this.timeGrid.renderNowIndicator(date);},unrenderNowIndicator:function(){this.timeGrid.unrenderNowIndicator();},updateSize:function(isResize){this.timeGrid.updateSize(isResize);View.prototype.updateSize.call(this,isResize);},updateWidth:function(){this.axisWidth=matchCellWidths(this.el.find('.fc-axis'));},setHeight:function(totalHeight,isAuto){var eventLimit;var scrollerHeight;var scrollbarWidths;this.bottomRuleEl.hide();this.scroller.clear();uncompensateScroll(this.noScrollRowEls);if(this.dayGrid){this.dayGrid.removeSegPopover();eventLimit=this.opt('eventLimit');if(eventLimit&&typeof eventLimit!=='number'){eventLimit=AGENDA_ALL_DAY_EVENT_LIMIT;}
if(eventLimit){this.dayGrid.limitRows(eventLimit);}}
if(!isAuto){scrollerHeight=this.computeScrollerHeight(totalHeight);this.scroller.setHeight(scrollerHeight);scrollbarWidths=this.scroller.getScrollbarWidths();if(scrollbarWidths.left||scrollbarWidths.right){compensateScroll(this.noScrollRowEls,scrollbarWidths);scrollerHeight=this.computeScrollerHeight(totalHeight);this.scroller.setHeight(scrollerHeight);}
this.scroller.lockOverflow(scrollbarWidths);if(this.timeGrid.getTotalSlatHeight()<scrollerHeight){this.bottomRuleEl.show();}}},computeScrollerHeight:function(totalHeight){return totalHeight-
subtractInnerElHeight(this.el,this.scroller.el);},computeInitialScroll:function(){var scrollTime=moment.duration(this.opt('scrollTime'));var top=this.timeGrid.computeTimeTop(scrollTime);top=Math.ceil(top);if(top){top++;}
return top;},queryScroll:function(){return this.scroller.getScrollTop();},setScroll:function(top){this.scroller.setScrollTop(top);},prepareHits:function(){this.timeGrid.prepareHits();if(this.dayGrid){this.dayGrid.prepareHits();}},releaseHits:function(){this.timeGrid.releaseHits();if(this.dayGrid){this.dayGrid.releaseHits();}},queryHit:function(left,top){var hit=this.timeGrid.queryHit(left,top);if(!hit&&this.dayGrid){hit=this.dayGrid.queryHit(left,top);}
return hit;},getHitSpan:function(hit){return hit.component.getHitSpan(hit);},getHitEl:function(hit){return hit.component.getHitEl(hit);},renderEvents:function(events){var dayEvents=[];var timedEvents=[];var daySegs=[];var timedSegs;var i;for(i=0;i<events.length;i++){if(events[i].allDay){dayEvents.push(events[i]);}
else{timedEvents.push(events[i]);}}
timedSegs=this.timeGrid.renderEvents(timedEvents);if(this.dayGrid){daySegs=this.dayGrid.renderEvents(dayEvents);}
this.updateHeight();},getEventSegs:function(){return this.timeGrid.getEventSegs().concat(this.dayGrid?this.dayGrid.getEventSegs():[]);},unrenderEvents:function(){this.timeGrid.unrenderEvents();if(this.dayGrid){this.dayGrid.unrenderEvents();}},renderDrag:function(dropLocation,seg){if(dropLocation.start.hasTime()){return this.timeGrid.renderDrag(dropLocation,seg);}
else if(this.dayGrid){return this.dayGrid.renderDrag(dropLocation,seg);}},unrenderDrag:function(){this.timeGrid.unrenderDrag();if(this.dayGrid){this.dayGrid.unrenderDrag();}},renderSelection:function(span){if(span.start.hasTime()||span.end.hasTime()){this.timeGrid.renderSelection(span);}
else if(this.dayGrid){this.dayGrid.renderSelection(span);}},unrenderSelection:function(){this.timeGrid.unrenderSelection();if(this.dayGrid){this.dayGrid.unrenderSelection();}}});var agendaTimeGridMethods={renderHeadIntroHtml:function(){var view=this.view;var weekText;if(view.opt('weekNumbers')){weekText=this.start.format(view.opt('smallWeekFormat'));return''+'<th class="fc-axis fc-week-number '+view.widgetHeaderClass+'" '+view.axisStyleAttr()+'>'+'<span>'+
htmlEscape(weekText)+'</span>'+'</th>';}
else{return'<th class="fc-axis '+view.widgetHeaderClass+'" '+view.axisStyleAttr()+'></th>';}},renderBgIntroHtml:function(){var view=this.view;return'<td class="fc-axis '+view.widgetContentClass+'" '+view.axisStyleAttr()+'></td>';},renderIntroHtml:function(){var view=this.view;return'<td class="fc-axis" '+view.axisStyleAttr()+'></td>';}};var agendaDayGridMethods={renderBgIntroHtml:function(){var view=this.view;return''+'<td class="fc-axis '+view.widgetContentClass+'" '+view.axisStyleAttr()+'>'+'<span>'+
(view.opt('allDayHtml')||htmlEscape(view.opt('allDayText')))+'</span>'+'</td>';},renderIntroHtml:function(){var view=this.view;return'<td class="fc-axis" '+view.axisStyleAttr()+'></td>';}};;;var AGENDA_ALL_DAY_EVENT_LIMIT=5;var AGENDA_STOCK_SUB_DURATIONS=[{hours:1},{minutes:30},{minutes:15},{seconds:30},{seconds:15}];fcViews.agenda={'class':AgendaView,defaults:{allDaySlot:true,allDayText:'all-day',slotDuration:'00:30:00',minTime:'00:00:00',maxTime:'24:00:00',slotEventOverlap:true}};fcViews.agendaDay={type:'agenda',duration:{days:1}};fcViews.agendaWeek={type:'agenda',duration:{weeks:1}};;;return FC;});
$.fullCalendar.lang("de",{buttonText:{month:"Monat",week:"Woche",day:"Tag",list:"Terminübersicht",today:"Heute"},allDayText:"Ganztägig",eventLimitText:function(n){return"+ weitere "+n;}});
/*
    The reservation calendar extends fullcalendar adding methods to allocate
    dates, select and then reserve them.
*/

var rc = $.reservationCalendar = {};
var defaultOptions = {
    /*
        Returns the allocations in a fullcalendar compatible events feed.
        See http://fullcalendar.io/docs/event_data/events_json_feed/
    */
    feed: null,

    /*
        Returns the reservations for the current resource.
    */
    reservations: null,

    /*
        The type of the calendar. Either 'room' or 'daypass'
    */
    type: null,

    /*
        The visible time range
    */
    minTime: '07:00:00',
    maxTime: '22:00:00',

    /*
        True if the calendar may be edited (by editors/admins)
    */
    editable: false,

    /*
        Url called when a new selection is made. For example:

            selectUrl: https://example.org/on-select

        Will be called like this:

            https://example.org/on-select
                ?start=2016-02-04T2200:00.000Z
                &end=2016-02-05T2300:00.000Z
                &whole_day=no
                &view=month
    */
    selectUrl: null,

    /*
        The view shown initially
    */
    view: 'month',

    /*
        The date shown initially
    */
    date: null,

    /*
        The event ids to highlight for a short while
    */
    highlights_min: null,
    highlights_max: null
};

rc.events = [
    'rc-allocations-changed',
    'rc-reservation-error',
    'rc-reservations-changed'
];

rc.passEventsToCalendar = function(calendar, target, source) {
    var cal = $(calendar);

    _.each(rc.events, function(eventName) {
        target.on(eventName, _.debounce(function(_e, data) {
            cal.trigger(eventName, [data, calendar, source]);
        }));
    });
};

rc.getFullcalendarOptions = function(options) {
    var rcOptions = $.extend(true, defaultOptions, options);

    // the fullcalendar default options
    var fcOptions = {
        allDaySlot: false,
        events: rcOptions.feed,
        minTime: rcOptions.minTime,
        maxTime: rcOptions.maxTime,
        editable: rcOptions.editable,
        selectable: rcOptions.editable,
        defaultView: rcOptions.view,
        highlights_min: rcOptions.highlights_min,
        highlights_max: rcOptions.highlights_max,
        afterSetup: [],
        viewRenderers: [],
        eventRenderers: [],
        reservations: rcOptions.reservations,
        reservationform: rcOptions.reservationform
    };

    // the reservation calendar type definition
    var views = [];

    switch (rcOptions.type) {
        case 'daypass':
            views = ['month'];
            fcOptions.header = {
                left: 'title today prev,next',
                center: '',
                right: ''
            };
            break;
        case 'room':
            views = ['month', 'agendaWeek', 'agendaDay'];
            fcOptions.header = {
                left: 'title today prev,next',
                center: '',
                right: views.join(',')
            };
            break;
        default:
            throw new Error("Unknown reservation calendar type: " + options.type);
    }

    // select a valid default view
    if (!_.contains(views, rcOptions.view)) {
        fcOptions.defaultView = views[0];
    }

    // implements editing
    if (rcOptions.editable) {

        // create events on selection
        fcOptions.select = function(start, end, _jsevent, view) {
            var url = new Url(rcOptions.selectUrl);
            url.query.start = start.toISOString();

            if (view.name === "month") {
                url.query.end = end.subtract(1, 'days').toISOString();
                url.query.whole_day = 'yes';
                url.query.view = view.name;
            } else {
                url.query.end = end.toISOString();
                url.query.whole_day = 'no';
                url.query.view = view.name;
            }
            window.location.href = url.toString();
        };

        // edit events on drag&drop, resize
        fcOptions.eventDrop = fcOptions.eventResize = function(event, _delta, _revertFunc, _jsEvent, _ui, view) {
            var url = new Url(event.editurl);
            url.query.start = event.start.toISOString();
            url.query.end = event.end.toISOString();
            url.query.view = view.name;
            location.href = url.toString();
        };

        // make sure other code can react if events are being changed
        fcOptions.eventDragStart = fcOptions.eventResizeStart = function(event) {
            event.is_changing = true;
        };
    }

    // after event rendering
    fcOptions.eventRenderers.push(rc.renderPartitions);
    fcOptions.eventRenderers.push(rc.highlightEvents);
    fcOptions.eventRenderers.push(rc.setupEventPopups);

    fcOptions.eventAfterRender = function(event, element, view) {
        var renderers = view.calendar.options.eventRenderers;
        for (var i = 0; i < renderers.length; i++) {
            renderers[i](event, element, view);
        }
    };

    // view change rendering
    fcOptions.viewRender = function(view, element) {
        var renderers = view.calendar.options.viewRenderers;
        for (var i = 0; i < renderers.length; i++) {
            renderers[i](view, element);
        }
    };

    // history handling
    rc.setupHistory(fcOptions);

    // reservation selection
    rc.setupReservationSelect(fcOptions);

    // setup allocation refresh handling
    fcOptions.afterSetup.push(rc.setupAllocationsRefetch);

    // switch to the correct date after the instance has been creted
    if (rcOptions.date) {
        fcOptions.afterSetup.push(function(calendar) {
            calendar.fullCalendar('gotoDate', rcOptions.date);
        });
    }

    return fcOptions;
};

$.fn.reservationCalendar = function(options) {
    var fcOptions = rc.getFullcalendarOptions($.extend(true, defaultOptions, options));

    return this.map(function(_ix, element) {

        var calendar = $(element).fullCalendar(fcOptions);

        for (var i = 0; i < fcOptions.afterSetup.length; i++) {
            fcOptions.afterSetup[i](calendar);
        }

        return calendar;
    });
};

// handles clicks on events
rc.setupEventPopups = function(event, element, view) {
    $(element).click(function(e) {
        var calendar = $(view.el.closest('.fc'));
        rc.removeAllPopups();
        rc.showActionsPopup(calendar, element, event);
        e.preventDefault();
        return false;
    });
};

// highlight events implementation
rc.highlightEvents = function(event, element, view) {
    var min = view.calendar.options.highlights_min;
    var max = view.calendar.options.highlights_max;

    if (min === null || max === null) {
        return;
    }

    if (min <= event.id && event.id <= max) {
        $(element).addClass('highlight');
    }
};

rc.setupAllocationsRefetch = function(calendar) {
    $(window).on('rc-allocations-changed', function() {
        calendar.fullCalendar('refetchEvents');
    });
};

// sends requests through intercooler
rc.request = function(calendar, url, attribute) {
    var el = $('<a />')
        .attr(attribute, url)
        .css('display', 'none')
        .appendTo($('body'));

    Intercooler.processNodes(el);

    el.on('complete.ic', function() {
        el.remove();
    });

    var source = $(calendar).find('.has-popup');
    rc.passEventsToCalendar(calendar, el, source);

    el.click();
};

rc.delete = function(calendar, url) {
    rc.request(calendar, url, 'ic-delete-from');
};

rc.post = function(calendar, url) {
    rc.request(calendar, url, 'ic-post-to');
};

// popup handler implementation
rc.showActionsPopup = function(calendar, element, event) {
    var wrapper = $('<div class="reservation-actions">');
    var reservation = $('<div class="reservation-form">').appendTo(wrapper);

    if (event.actions.length > 0) {
        $('<h3 />').text(locale('Allocation')).appendTo(wrapper);
        $(event.actions.join('')).appendTo(wrapper);
    }

    ReservationForm.render(reservation.get(0), event, rc.previousReservationState, function(state) {
        var url = new Url(event.reserveurl);
        url.query.start = state.start;
        url.query.end = state.end;
        url.query.quota = state.quota;
        url.query.whole_day = state.wholeDay && '1' || '0';

        rc.post(calendar, url.toString());

        $(this).closest('.popup').popup('hide');
    });

    rc.showPopup(calendar, element, wrapper);
};

rc.showErrorPopup = function(calendar, element, message) {
    rc.showPopup(calendar, element, message, 'top', ['error']);
};

rc.showPopup = function(calendar, element, content, position, extraClasses) {

    $(element).closest('.fc-event').addClass('has-popup');

    var options = {
        autoopen: true,
        tooltipanchor: element,
        type: 'tooltip',
        onopen: function() {
            rc.onPopupOpen.call(this, calendar);
        },
        onclose: function() {
            $(element).closest('.fc-event').removeClass('has-popup');
        },
        closebutton: true,
        closebuttonmarkup: '<a href="#" class="close">×</a>'
    };

    switch (position || 'right') {
        case 'top':
            options.horizontal = 'center';
            options.vertical = 'top';
            options.extraClasses = _.union(['top'], extraClasses || []);
            options.offsettop = -5;
            options.offsetleft = 20; // for some reason the popup's a bit off center
            break;
        case 'right':
            options.horizontal = 'right';
            options.vertical = 'middle';
            options.extraClasses = _.union(['right'], extraClasses || []);
            options.offsetleft = -10;
            break;
        default:
            throw Error("Unknown position: " + position);
    }

    $('<div class="popup" />').append(content).popup(options);
};

rc.onPopupOpen = function(calendar) {
    var popup = $(this);
    var options = popup.data('popupoptions');

    _.each(options.extraClasses, function(className) {
        popup.addClass(className);
    });

    var links = popup.find('a:not(.internal)');

    // hookup all links with intercool
    links.each(function(_ix, link) {
        Intercooler.processNodes($(link));
    });

    // close the popup after any click on a link
    _.each(['ic.success', 'mouseup'], function(eventName) {
        $(links).on(eventName, _.debounce(function() {
            popup.popup('hide');
        }));
    });

    // hookup the confirmation dialog
    var confirm_links = popup.find('a.confirm');
    confirm_links.confirmation();

    // pass all reservationcalendar events to the calendar
    rc.passEventsToCalendar(calendar, links, options.tooltipanchor);
};

rc.removeAllPopups = function() {
    $('.popup').popup('hide').remove();
};

// setup browser history handling
rc.setupHistory = function(fcOptions) {
    var isPopping = false;
    var isFirst = true;

    fcOptions.viewRenderers.push(function(view) {
        if (isPopping) {
            return;
        }

        var url = new Url(window.location.href);
        url.query.view = view.name;
        url.query.date = view.intervalStart.format('YYYYMMDD');

        $('a.calendar-dependent').each(function(_ix, el) {
            var dependentUrl = new Url($(el).attr('href'));
            dependentUrl.query.view = url.query.view;
            dependentUrl.query.date = url.query.date;
            $(el).attr('href', dependentUrl.toString());
        });

        var state = [
            {
                'view': view.name,
                'date': view.intervalStart
            },
            document.title + ' ' + view.title,
            url.toString()
        ];

        if (isFirst) {
            window.history.replaceState.apply(window.history, state);
            isFirst = false;
        } else {
            window.history.pushState.apply(window.history, state);
        }
    });

    fcOptions.afterSetup.push(function(calendar) {
        window.onpopstate = function(event) {
            if (event.state === null) {
                return;
            }

            isPopping = true;
            calendar.fullCalendar('changeView', event.state.view);
            calendar.fullCalendar('gotoDate', event.state.date);
            isPopping = false;
        };
    });
};

// setup the reservation selection on the right
rc.setupReservationSelect = function(fcOptions) {
    var selection = null;

    fcOptions.afterSetup.push(function(calendar) {
        var view = $(calendar).find('.fc-view-container');

        selection = $('<div class="reservation-selection"></div>')
            .insertAfter(view);
        $('<div class="clearfix"></div>').insertAfter(selection);

        calendar.fullCalendar('option', 'aspectRatio', 1.1415926);

        calendar.on('rc-reservation-error', function(_e, data, _calendar, target) {
            var event = calendar.find('.has-popup');

            if (!target) {
                if (event.length !== 0) {
                    target = event;
                } else {
                    target = calendar.find('.fc-view');
                }
            }

            target = target || calendar.find('.has-popup') || calendar.find('.fc-view');
            rc.showErrorPopup(calendar, target, data.message);
        });

        calendar.on('rc-reservations-changed', function() {
            $.getJSON(fcOptions.reservations + '&ie-cache=' + (new Date()).getTime(), function(reservations) {
                ReservationSelection.render(selection.get(0), calendar, reservations, fcOptions.reservationform);
                rc.loadPreviousReservationState(reservations);
            });
        });

        calendar.trigger('rc-reservations-changed');
    });
};

// takes the loaded reservations and deduces the previous state from them
rc.loadPreviousReservationState = function(reservations) {
    if (reservations.length > 0) {
        reservations = _.sortBy(reservations, function(reservation) {
            return reservation.created;
        });

        for (var i = reservations.length - 1; i >= 0; i--) {
            if (reservations[i].time.match(/^\d{2}:\d{2} - \d{2}:\d{2}$/)) {
                rc.previousReservationState = {
                    'start': reservations[i].time.split(' - ')[0],
                    'end': reservations[i].time.split(' - ')[1]
                };

                break;
            }
        }
    } else {
        rc.previousReservationState = {};
    }
};

// renders the occupied partitions on an event
rc.renderPartitions = function(event, element, calendar) {

    if (event.is_moving) {
        return;
    }

    var free = _.template('<div style="height:<%= height %>%;" class="partition-free"></div>');
    var used = _.template('<div style="height:<%= height %>%;" class="partition-occupied"></div>');
    var partition_block = _.template('<div style="height:<%= height %>px;" class="partitions"><%= partitions %></div>');

    // build the individual partitions
    var event_partitions = rc.adjustPartitions(
        event,
        moment.duration(calendar.options.minTime).hours(),
        moment.duration(calendar.options.maxTime).hours()
    );

    var partitions = '';
    _.each(event_partitions, function(partition) {
        var reserved = partition[1];
        if (reserved === false) {
            partitions += free({height: partition[0]});
        } else {
            partitions += used({height: partition[0]});
        }
    });

    // locks the height during resizing
    var height = element.outerHeight(true);
    if (event.is_changing) {
        height = event.height;
        $(element).addClass('changing');
    } else {
        event.height = height;
    }

    // render the whole block
    var html = $(partition_block({height: height, partitions: partitions}));
    var offset = 0;
    var duration = event.end - event.start;

    html.children().each(function(ix, partition) {
        var reserved = event.partitions[ix][1];
        var percent = event.partitions[ix][0] / 100;

        if (!reserved) {
            var subevent = _.clone(event);

            subevent.start = moment(event.start + duration * offset);
            subevent.end = moment(event.start + duration * (offset + percent));
            rc.setupEventPopups(subevent, partition, calendar);
        }

        offset += percent;
    });

    $('.fc-bg', element).wrapInner(html);
};

// partitions are relative to the event. Since depending on the
// calendar only part of an event may be shown, we need to account
// for that fact. This function takes the event, and the range of
// the calendar and adjusts the partitions if necessary.
rc.adjustPartitions = function(event, min_hour, max_hour) {

    if (_.isUndefined(event.partitions)) {
        return event.partitions;
    }

    // clone the partitions
    var partitions = _.map(event.partitions, _.clone);
    var start_hour = event.start.hours();
    var end_hour = event.end.hours() === 0 ? 24 : event.end.hours();
    var duration = end_hour - start_hour;

    // if the event fits inside the calendar hours, all is ok
    if (min_hour <= start_hour && end_hour <= max_hour) {
        return partitions;
    }

    // if the whole event contains only one partition, no move will
    // change anything
    if (partitions.length <= 1) {
        return partitions;
    }

    // the event is rendered within the calendar, with the top and
    // bottom cut off. The partitions are calculated assuming the
    // event is being rendered as a whole. To adjust we cut the
    // bottom and top from the partitions and blow up the whole event.
    //
    // It made sense when I wrote the initial implementation :)
    var percentage_per_hour = 1 / duration * 100;
    var top_margin = 0, bottom_margin = 0;

    if (start_hour < min_hour) {
        top_margin = (min_hour - start_hour) * percentage_per_hour;
    }
    if (end_hour > max_hour) {
        bottom_margin = (end_hour - max_hour) * percentage_per_hour;
    }

    partitions = rc.removeMarginFromPartitions(partitions, top_margin);
    partitions.reverse();

    partitions = rc.removeMarginFromPartitions(partitions, bottom_margin);
    partitions.reverse();

    // blow up the result to 100%;
    var total = rc.sumPartitions(partitions);
    _.each(partitions, function(partition) {
        partition[0] = partition[0] / total * 100;
    });

    return partitions;
};

// remove the given margin from the top of the partitions array
// the margin is given as a percentage
rc.removeMarginFromPartitions = function(partitions, margin) {

    if (margin === 0) {
        return partitions;
    }

    var removed_total = 0;
    var original_margin = margin;

    for (var i = 0; i < partitions.length; i++) {
        if (rc.roundNumber(partitions[i][0]) >= rc.roundNumber(margin)) {
            partitions[i][0] = partitions[i][0] - margin;
            break;
        } else {
            removed_total += partitions[i][0];
            margin -= partitions[i][0];
            partitions.splice(i, 1);

            i -= 1;

            if (removed_total >= original_margin) {
                break;
            }
        }
    }

    return partitions;
};

rc.roundNumber = function(num) {
    return +Number(Math.round(num + "e+2") + "e-2");
};

rc.sumPartitions = function(partitions) {
    return _.reduce(partitions, function(running_total, p) {
        return running_total + p[0];
    }, 0);
};

/*
    Shows the list of reservations to be confirmed.
*/
ReservationSelection = React.createClass({displayName: "ReservationSelection",
    handleClick: function(reservation) {
        rc.delete($(this.props.calendar), reservation.delete);
    },
    handleSubmit: function() {
        if (this.props.reservations.length) {
            window.location = this.props.reservationform;
        }
    },
    render: function() {
        var self = this;

        return (
            React.createElement("div", {className: "reservation-selection-inner"}, 
                React.createElement("h3", null, locale("Dates")), 
                
                    this.props.reservations.length === 0 &&
                        React.createElement("p", null, locale("Select allocations in the calendar to reserve them")), 
                
                
                    this.props.reservations.length > 0 &&
                        React.createElement("ul", null, 
                            _.map(this.props.reservations, function(r, ix) {
                                var boundClick = self.handleClick.bind(self, r);
                                var date = moment(r.date).locale(window.locale.language);
                                return (
                                    React.createElement("li", {key: ix, className: "reservation"}, 
                                        React.createElement("span", {className: "reservation-date", "data-quota": r.quota}, date.format('ddd LL')), 
                                        React.createElement("span", {className: "reservation-time"}, r.time), 
                                        React.createElement("a", {className: "delete", onClick: boundClick}, locale('Remove'))
                                    )
                                );
                            })
                        ), 
                
                React.createElement("a", {onClick: self.handleSubmit, className: this.props.reservations.length === 0 && 'disabled button secondary' || 'button'}, 
                    locale("Reserve")
                )
            )
        );
    }
});

ReservationSelection.render = function(element, calendar, reservations, reservationform) {
    React.render(React.createElement(ReservationSelection, {calendar: calendar, reservations: reservations, reservationform: reservationform}), element);
};

/*
    Allows to fine-adjust the reservation before adding it.
*/
ReservationForm = React.createClass({displayName: "ReservationForm",
    getInitialState: function() {
        var state = {
            quota: 1
        };

        // if the event is a 100% available and a full day, we pre-select
        // the whole-day button and empty the times so the user has to enter
        // a time when he switches
        if (this.props.wholeDay && this.props.fullyAvailable) {
            state.start = "";
            state.end = "";
            state.wholeDay = true;
        } else {
            state.start = this.props.start.format('HH:mm');
            state.end = this.props.end.format('HH:mm');
            state.wholeDay = false;
        }

        state.end = state.end === '00:00' && '24:00' || state.end;

        return state;
    },
    componentDidMount: function() {
        var node = $(this.getDOMNode());

        // the timeout is set to 100ms because the popup will do its own focusing
        // after 50ms (we could use it, but we want to focus AND select)
        setTimeout(function() {
            node.find('input:first').focus().select();
        }, 100);
    },
    handleInputChange: function(e) {
        var state = _.extend({}, this.state);
        var name = e.target.getAttribute('name');

        switch (name) {
            case 'reserve-whole-day':
                state.wholeDay = e.target.value === 'yes';
                break;
            case 'start':
                state.start = e.target.value;
                break;
            case 'end':
                state.end = e.target.value === '00:00' && '24:00' || e.target.value;
                break;
            case 'count':
                state.quota = parseInt(e.target.value, 10);
                break;
            default:
                throw Error("Unknown input element: " + name);
        }

        this.setState(state);
    },
    handleButton: function(e) {
        var node = this.getDOMNode();
        var self = this;

        $(node).find('input').each(function(_ix, el) {
            $(el).blur();
        });

        setTimeout(function() {
            self.props.onSubmit.call(node, self.state);
        }, 0);

        e.preventDefault();
    },
    handleSetPreviousTime: function(e) {
        var previousState = this.props.previousReservationState;
        var node = $(this.getDOMNode());
        var inputs = node.find('[name="start"],[name="end"]');

        $(inputs[0]).val(previousState.start);
        $(inputs[1]).val(previousState.end);

        // deselect 'whole-day' if it exists
        node.find('[name="reserve-whole-day"]').filter('[value="no"]').prop('checked', true);

        // briefly highlight the inputs
        inputs.addClass('highlighted');
        setTimeout(function() {
            inputs.removeClass('highlighted');
        }, 500);

        var state = _.extend({}, this.state);
        state.start = previousState.start;
        state.end = previousState.end;
        state.wholeDay = false;

        this.setState(state);

        e.preventDefault();
    },
    handleTimeInputFocus: function(e) {
        if (!Modernizr.inputtypes.time) {
            e.target.select();
            e.preventDefault();
        }
    },
    handleTimeInputMouseUp: function(e) {
        if (!Modernizr.inputtypes.time) {
            e.preventDefault();
        }
    },
    handleTimeInputBlur: function(e) {
        if (!Modernizr.inputtypes.time) {
            e.target.value = this.inferTime(e.target.value);
            this.handleInputChange(e);
        }
    },
    inferTime: function(time) {
        time = time.replace(':', '');

        if (time.match(/^\d{1}$/)) {
            time = '0' + time + '00';
        } else if (time.match(/^\d{2}$/)) {
            time += '00';
        } else if (time.match(/^\d{3}$/)) {
            time += '0';
        }

        if (time.match(/^\d{4}$/)) {
            time = time.slice(0, 2) + ':' + time.slice(2, 4);
        }

        return time;
    },
    parseTime: function(date, time) {
        time = this.inferTime(time);

        if (!time.match(/^[0-2]{1}[0-9]{1}:?[0-5]{1}[0-9]{1}$/)) {
            return null;
        }

        var hour = parseInt(time.split(':')[0], 10);
        var minute = parseInt(time.split(':')[1], 10);

        if (hour < 0 || 24 < hour) {
            return null;
        }

        if (minute < 0 || 60 < minute) {
            return null;
        }

        date.hour(hour);
        date.minute(minute);

        return date;
    },
    isValidStart: function(start) {
        var startdate = this.parseTime(this.props.start.clone(), start);
        return startdate !== null && this.props.start <= startdate;
    },
    isValidEnd: function(end) {
        var enddate = this.parseTime(this.props.start.clone(), end);
        return enddate !== null && enddate <= this.props.end;
    },
    isValidQuota: function(quota) {
        return quota > 0 && quota <= this.props.quotaLeft;
    },
    isValidState: function() {
        if (this.props.partlyAvailable) {
            if (this.props.wholeDay && this.state.wholeDay) {
                return true;
            } else {
                return this.isValidStart(this.state.start) && this.isValidEnd(this.state.end);
            }
        } else {
            return this.isValidQuota(this.state.quota);
        }
    },
    render: function() {
        var buttonEnabled = this.isValidState();
        var showWholeDay = this.props.partlyAvailable && this.props.wholeDay;
        var showTimeRange = this.props.partlyAvailable && (!this.props.wholeDay || !this.state.wholeDay);
        var hasPreviousTimeToOffer = !_.isEmpty(this.props.previousReservationState) &&
            (
                this.props.previousReservationState.start !== this.state.start ||
                this.props.previousReservationState.end !== this.state.end
            );

        var showPreviousTime = (showTimeRange || showWholeDay) && hasPreviousTimeToOffer;
        var showQuota = !this.props.partlyAvailable;

        return (
            React.createElement("form", null, 
                showWholeDay && (
                    React.createElement("div", {className: "field"}, 
                        React.createElement("span", {className: "label-text"}, locale("Whole day")), 

                        React.createElement("input", {id: "reserve-whole-day-yes", 
                            name: "reserve-whole-day", 
                            type: "radio", 
                            value: "yes", 
                            checked: this.state.wholeDay, 
                            onChange: this.handleInputChange}
                        ), 
                        React.createElement("label", {htmlFor: "reserve-whole-day-yes"}, locale("Yes")), 
                        React.createElement("input", {id: "reserve-whole-day-no", 
                            name: "reserve-whole-day", 
                            type: "radio", 
                            value: "no", 
                            checked: !this.state.wholeDay, 
                            onChange: this.handleInputChange}
                        ), 
                        React.createElement("label", {htmlFor: "reserve-whole-day-no"}, locale("No"))
                    )
                ), 

                showTimeRange && (
                    React.createElement("div", {className: "field split"}, 
                        React.createElement("div", null, 
                            React.createElement("label", {htmlFor: "start"}, locale("From")), 
                            React.createElement("input", {name: "start", type: "time", size: "4", 
                                defaultValue: this.state.start, 
                                onChange: this.handleInputChange, 
                                onFocus: this.handleTimeInputFocus, 
                                onMouseUp: this.handleTimeInputMouseUp, 
                                onBlur: this.handleTimeInputBlur, 
                                className: this.isValidStart(this.state.start) && 'valid' || 'invalid'}
                            )
                        ), 
                        React.createElement("div", null, 
                            React.createElement("label", {htmlFor: "end"}, locale("Until")), 
                            React.createElement("input", {name: "end", type: "time", size: "4", 
                                defaultValue: this.state.end, 
                                onChange: this.handleInputChange, 
                                onFocus: this.handleTimeInputFocus, 
                                onMouseUp: this.handleTimeInputMouseUp, 
                                onBlur: this.handleTimeInputBlur, 
                                className: this.isValidEnd(this.state.end) && 'valid' || 'invalid'}
                            )
                        )
                    )
                ), 

                showPreviousTime && (
                    React.createElement("a", {href: "#", onClick: this.handleSetPreviousTime, className: "select-previous-time internal"}, 
                        React.createElement("i", {className: "fa fa-chevron-circle-right", "aria-hidden": "true"}), 
                        React.createElement("span", null, this.props.previousReservationState.start), 
                        React.createElement("span", null, " - "), 
                        React.createElement("span", null, this.props.previousReservationState.end)
                    )
                ), 

                showQuota && (
                    React.createElement("div", {className: "field"}, 
                        React.createElement("div", null, 
                            React.createElement("label", {htmlFor: "count"}, locale("Count")), 
                            React.createElement("input", {name: "count", type: "number", size: "4", 
                                min: "1", 
                                max: this.props.quotaLeft, 
                                defaultValue: this.state.quota, 
                                onChange: this.handleInputChange}
                            )
                        )
                    )
                ), 

                React.createElement("button", {className: buttonEnabled && "button" || "button secondary", disabled: !buttonEnabled, onClick: this.handleButton}, locale("Add"))
            )
        );
    }
});

ReservationForm.render = function(element, event, previousReservationState, onSubmit) {

    var fullyAvailable = event.partitions.length === 1 && event.partitions[0][1] === false;

    React.render(
        React.createElement(ReservationForm, {
            partlyAvailable: event.partlyAvailable, 
            quota: event.quota, 
            quotaLeft: event.quotaLeft, 
            start: event.start, 
            end: event.end, 
            wholeDay: event.wholeDay, 
            fullyAvailable: fullyAvailable, 
            previousReservationState: previousReservationState, 
            onSubmit: onSubmit}
        ),
    element);
};

var setupReservationCalendar=function(calendar){calendar.reservationCalendar({feed:calendar.data('feed'),type:calendar.data('type'),minTime:calendar.data('min-time'),maxTime:calendar.data('min-time'),editable:calendar.data('editable'),selectUrl:calendar.data('select-url'),editUrl:calendar.data('edit-url'),view:calendar.data('view'),date:calendar.data('date'),highlights_min:calendar.data('highlights-min'),highlights_max:calendar.data('highlights-max'),reservations:calendar.data('reservations'),reservationform:calendar.data('reservationform')});};$(document).ready(function(){_.each(_.map($('.calendar'),$),setupReservationCalendar);});