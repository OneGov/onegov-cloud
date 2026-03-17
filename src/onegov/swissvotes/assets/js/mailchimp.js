(function($) {window.fnames = new Array(); window.ftypes = new Array();fnames[0]='EMAIL';ftypes[0]='email';fnames[1]='FNAME';ftypes[1]='text';fnames[2]='LNAME';ftypes[2]='text';fnames[3]='ADDRESS';ftypes[3]='address';fnames[4]='PHONE';ftypes[4]='phone';fnames[6]='COMPANY';ftypes[6]='text';}(jQuery));var $mcj = jQuery.noConflict(true);
    // SMS Phone Multi-Country Functionality
    if(!window.MC) {
      window.MC = {};
    }
    window.MC.smsPhoneData = {
      defaultCountryCode: 'CH',
      programs: [],
      smsProgramDataCountryNames: []
    };

    function getCountryUnicodeFlag(countryCode) {
       return countryCode.toUpperCase().replace(/./g, (char) => String.fromCodePoint(char.charCodeAt(0) + 127397))
    };

    // HTML sanitization function to prevent XSS
    function sanitizeHtml(str) {
      if (typeof str !== 'string') return '';
      return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;')
        .replace(/\//g, '&#x2F;');
    }

    // URL sanitization function to prevent javascript: and data: URLs
    function sanitizeUrl(url) {
      if (typeof url !== 'string') return '';
      const trimmedUrl = url.trim().toLowerCase();
      if (trimmedUrl.startsWith('javascript:') || trimmedUrl.startsWith('data:') || trimmedUrl.startsWith('vbscript:')) {
        return '#';
      }
      return url;
    }

    const getBrowserLanguage = () => {
      if (!window?.navigator?.language?.split('-')[1]) {
        return window?.navigator?.language?.toUpperCase();
      }
      return window?.navigator?.language?.split('-')[1];
    };

    function getDefaultCountryProgram(defaultCountryCode, smsProgramData) {
      if (!smsProgramData || smsProgramData.length === 0) {
        return null;
      }

      const browserLanguage = getBrowserLanguage();

      if (browserLanguage) {
        const foundProgram = smsProgramData.find(
          (program) => program?.countryCode === browserLanguage,
        );
        if (foundProgram) {
          return foundProgram;
        }
      }

      if (defaultCountryCode) {
        const foundProgram = smsProgramData.find(
          (program) => program?.countryCode === defaultCountryCode,
        );
        if (foundProgram) {
          return foundProgram;
        }
      }

      return smsProgramData[0];
    }

    function updateSmsLegalText(countryCode, fieldName) {
      if (!countryCode || !fieldName) {
        return;
      }
      
      const programs = window?.MC?.smsPhoneData?.programs;
      if (!programs || !Array.isArray(programs)) {
        return;
      }
      
      const program = programs.find(program => program?.countryCode === countryCode);
      if (!program || !program.requiredTemplate) {
        return;
      }
      
      const legalTextElement = document.querySelector('#legal-text-' + fieldName);
      if (!legalTextElement) {
        return;
      }
      
      // Remove HTML tags and clean up the text
      const divRegex = new RegExp('</?[div][^>]*>', 'gi');
      const fullAnchorRegex = new RegExp('<a.*?</a>', 'g');
      const anchorRegex = new RegExp('<a href="(.*?)" target="(.*?)">(.*?)</a>');
      
      const template = program.requiredTemplate.replace(divRegex, '');
      
      

      legalTextElement.textContent = '';
      const parts = template.split(/(<a href=".*?" target=".*?">.*?<\/a>)/g);
      parts.forEach(function(part) {
        if (!part) {
          return;
        }
        const anchorMatch = part.match(/<a href="(.*?)" target="(.*?)">(.*?)<\/a>/);
        if (anchorMatch) {
          const linkElement = document.createElement('a');
          linkElement.href = sanitizeUrl(anchorMatch[1]);
          linkElement.target = sanitizeHtml(anchorMatch[2]);
          linkElement.textContent = sanitizeHtml(anchorMatch[3]);
          legalTextElement.appendChild(linkElement);
        } else {
          legalTextElement.appendChild(document.createTextNode(part));
        }
      });
          
    }

    function generateDropdownOptions(smsProgramData) {
      if (!smsProgramData || smsProgramData.length === 0) {
        return '';
      }
      
      return smsProgramData.map(program => {
        const flag = getCountryUnicodeFlag(program.countryCode);
        const countryName = getCountryName(program.countryCode);
        const callingCode = program.countryCallingCode || '';
        // Sanitize all values to prevent XSS
        const sanitizedCountryCode = sanitizeHtml(program.countryCode || '');
        const sanitizedCountryName = sanitizeHtml(countryName || '');
        const sanitizedCallingCode = sanitizeHtml(callingCode || '');
        return '<option value="' + sanitizedCountryCode + '">' + sanitizedCountryName + ' ' + sanitizedCallingCode + '</option>';
      }).join('');
    }

    function getCountryName(countryCode) {
      if (window.MC?.smsPhoneData?.smsProgramDataCountryNames && Array.isArray(window.MC.smsPhoneData.smsProgramDataCountryNames)) {
        for (let i = 0; i < window.MC.smsPhoneData.smsProgramDataCountryNames.length; i++) {
          if (window.MC.smsPhoneData.smsProgramDataCountryNames[i].code === countryCode) {
            return window.MC.smsPhoneData.smsProgramDataCountryNames[i].name;
          }
        }
      }
      return countryCode;
    }

    function getDefaultPlaceholder(countryCode) {
      if (!countryCode || typeof countryCode !== 'string') {
        return '+1 000 000 0000'; // Default US placeholder
      }
      
            var mockPlaceholders = [
        {
          countryCode: 'US',
          placeholder: '+1 000 000 0000',
          helpText: 'Include the US country code +1 before the phone number',
        },
        {
          countryCode: 'GB',
          placeholder: '+44 0000 000000',
          helpText: 'Include the GB country code +44 before the phone number',
        },
        {
          countryCode: 'CA',
          placeholder: '+1 000 000 0000',
          helpText: 'Include the CA country code +1 before the phone number',
        },
        {
          countryCode: 'AU',
          placeholder: '+61 000 000 000',
          helpText: 'Include the AU country code +61 before the phone number',
        },
        {
          countryCode: 'DE',
          placeholder: '+49 000 0000000',
          helpText: 'Fügen Sie vor der Telefonnummer die DE-Ländervorwahl +49 ein',
        },
        {
          countryCode: 'FR',
          placeholder: '+33 0 00 00 00 00',
          helpText: 'Incluez le code pays FR +33 avant le numéro de téléphone',
        },
        {
          countryCode: 'ES',
          placeholder: '+34 000 000 000',
          helpText: 'Incluya el código de país ES +34 antes del número de teléfono',
        },
        {
          countryCode: 'NL',
          placeholder: '+31 0 00000000',
          helpText: 'Voeg de NL-landcode +31 toe vóór het telefoonnummer',
        },
        {
          countryCode: 'BE',
          placeholder: '+32 000 00 00 00',
          helpText: 'Incluez le code pays BE +32 avant le numéro de téléphone',
        },
        {
          countryCode: 'CH',
          placeholder: '+41 00 000 00 00',
          helpText: 'Fügen Sie vor der Telefonnummer die CH-Ländervorwahl +41 ein',
        },
        {
          countryCode: 'AT',
          placeholder: '+43 000 000 0000',
          helpText: 'Fügen Sie vor der Telefonnummer die AT-Ländervorwahl +43 ein',
        },
        {
          countryCode: 'IE',
          placeholder: '+353 00 000 0000',
          helpText: 'Include the IE country code +353 before the phone number',
        },
        {
          countryCode: 'IT',
          placeholder: '+39 000 000 0000',
          helpText: 'Includere il prefisso internazionale IT +39 prima del numero di telefono',
        },
        {
          countryCode: 'NO',
          placeholder: '+47 000 00 000',
          helpText: 'Inkluder NO landskode +47 før telefonnummeret',
        },
        {
          countryCode: 'SE',
          placeholder: '+46 00 000 00 00',
          helpText: 'Inkludera SE landskod +46 före telefonnumret',
        },
        {
          countryCode: 'DK',
          placeholder: '+45 00 00 00 00',
          helpText: 'Inkluder DK landekode +45 før telefonnummeret',
        },
        {
          countryCode: 'FI',
          placeholder: '+358 00 000 0000',
          helpText: 'Sisällytä FI-maakoodi +358 ennen puhelinnumeroa',
        },
        {
          countryCode: 'EE',
          placeholder: '+372 0000 0000',
          helpText: 'Lisage EE riigikood +372 telefoninumbri ette',
        },
        {
          countryCode: 'PL',
          placeholder: '+48 000 000 000',
          helpText: 'Podaj numer kierunkowy PL +48 przed numerem telefonu',
        },
        {
          countryCode: 'SK',
          placeholder: '+421 000 000 000',
          helpText: 'Pred telefónne číslo uveďte kód krajiny SK +421',
        },
        {
          countryCode: 'LV',
          placeholder: '+371 0000 0000',
          helpText: 'Iekļaujiet LV valsts kodu +371 pirms tālruņa numura',
        },
        {
          countryCode: 'LT',
          placeholder: '+370 0000 0000',
          helpText: 'Įtraukite LT šalies kodą +370 prieš telefono numerį',
        },
        {
          countryCode: 'GR',
          placeholder: '+30 000 000 0000',
          helpText: 'Συμπεριλάβετε τον κωδικό χώρας GR +30 πριν από τον αριθμό τηλεφώνου',
        },
        {
          countryCode: 'PT',
          placeholder: '+351 000 000 000',
          helpText: 'Inclua o código de país PT +351 antes do número de telefone',
        },
        {
          countryCode: 'HR',
          placeholder: '+385 00 000 0000',
          helpText: 'Uključite HR pozivni broj države +385 prije telefonskog broja',
        },
        {
          countryCode: 'SI',
          placeholder: '+386 00 000 000',
          helpText: 'Vključite SI kodo države +386 pred telefonsko številko',
        },
        {
          countryCode: 'IS',
          placeholder: '+354 000 0000',
          helpText: 'Láttu IS landsnúmer +354 fylgja á undan símanúmerinu',
        },
        {
          countryCode: 'LU',
          placeholder: '+352 000 000 000',
          helpText: 'Incluez le code pays LU +352 avant le numéro de téléphone',
        },
        {
          countryCode: 'MC',
          placeholder: '+377 00 00 00 00',
          helpText: 'Incluez le code pays MC +377 avant le numéro de téléphone',
        },
        {
          countryCode: 'AD',
          placeholder: '+376 000 000',
          helpText: 'Incloeu el codi de país AD +376 abans del número de telèfon',
        },
        {
          countryCode: 'JE',
          placeholder: '+44 0000 000000',
          helpText: 'Include the JE country code +44 before the phone number',
        },
        {
          countryCode: 'IM',
          placeholder: '+44 0000 000000',
          helpText: 'Include the IM country code +44 before the phone number',
        },
        {
          countryCode: 'GG',
          placeholder: '+44 0000 000000',
          helpText: 'Include the GG country code +44 before the phone number',
        },
        {
          countryCode: 'AL',
          placeholder: '+355 00 000 0000',
          helpText: 'Përfshini kodin e vendit AL +355 para numrit të telefonit',
        },
        {
          countryCode: 'SM',
          placeholder: '+378 0000 000000',
          helpText: 'Includere il prefisso internazionale SM +378 prima del numero di telefono',
        },
        {
          countryCode: 'FO',
          placeholder: '+298 000000',
          helpText: 'Inkluder FO landekode +298 før telefonnummeret',
        },
        {
          countryCode: 'MT',
          placeholder: '+356 0000 0000',
          helpText: 'Include the MT country code +356 before the phone number',
        },
        {
          countryCode: 'LI',
          placeholder: '+423 000 0000',
          helpText: 'Fügen Sie vor der Telefonnummer die LI-Ländervorwahl +423 ein',
        },
        {
          countryCode: 'GI',
          placeholder: '+350 000 00000',
          helpText: 'Include the GI country code +350 before the phone number',
        },
        {
          countryCode: 'MD',
          placeholder: '+373 00 000 000',
          helpText: 'Includeți codul de țară MD +373 înaintea numărului de telefon',
        },
        {
          countryCode: 'HU',
          placeholder: '+36 00 000 0000',
          helpText: 'A telefonszám előtt adja meg a HU országkódot +36',
        },
        {
          countryCode: 'NZ',
          placeholder: '+64 00 000 0000',
          helpText: 'Include the NZ country code +64 before the phone number',
        },
        {
          countryCode: 'ME',
          placeholder: '+382 00 000 000',
          helpText: 'Uključite ME pozivni broj države +382 prije telefonskog broja',
        },
      ];

      const selectedPlaceholder = mockPlaceholders.find(function(item) {
        return item && item.countryCode === countryCode;
      });
      
      return selectedPlaceholder ? selectedPlaceholder.placeholder : mockPlaceholders[0].placeholder;
    }

    function updatePlaceholder(countryCode, fieldName) {
      if (!countryCode || !fieldName) {
        return;
      }
      
      const phoneInput = document.querySelector('#mce-' + fieldName);
      if (!phoneInput) {
        return;
      }
      
      const placeholder = getDefaultPlaceholder(countryCode);
      if (placeholder) {
        phoneInput.placeholder = placeholder;
      }
    }

    function updateCountryCodeInstruction(countryCode, fieldName) {
      updatePlaceholder(countryCode, fieldName);
      
    }

    function getDefaultHelpText(countryCode) {
      var mockPlaceholders = [
        {
          countryCode: 'US',
          placeholder: '+1 000 000 0000',
          helpText: 'Include the US country code +1 before the phone number',
        },
        {
          countryCode: 'GB',
          placeholder: '+44 0000 000000',
          helpText: 'Include the GB country code +44 before the phone number',
        },
        {
          countryCode: 'CA',
          placeholder: '+1 000 000 0000',
          helpText: 'Include the CA country code +1 before the phone number',
        },
        {
          countryCode: 'AU',
          placeholder: '+61 000 000 000',
          helpText: 'Include the AU country code +61 before the phone number',
        },
        {
          countryCode: 'DE',
          placeholder: '+49 000 0000000',
          helpText: 'Fügen Sie vor der Telefonnummer die DE-Ländervorwahl +49 ein',
        },
        {
          countryCode: 'FR',
          placeholder: '+33 0 00 00 00 00',
          helpText: 'Incluez le code pays FR +33 avant le numéro de téléphone',
        },
        {
          countryCode: 'ES',
          placeholder: '+34 000 000 000',
          helpText: 'Incluya el código de país ES +34 antes del número de teléfono',
        },
        {
          countryCode: 'NL',
          placeholder: '+31 0 00000000',
          helpText: 'Voeg de NL-landcode +31 toe vóór het telefoonnummer',
        },
        {
          countryCode: 'BE',
          placeholder: '+32 000 00 00 00',
          helpText: 'Incluez le code pays BE +32 avant le numéro de téléphone',
        },
        {
          countryCode: 'CH',
          placeholder: '+41 00 000 00 00',
          helpText: 'Fügen Sie vor der Telefonnummer die CH-Ländervorwahl +41 ein',
        },
        {
          countryCode: 'AT',
          placeholder: '+43 000 000 0000',
          helpText: 'Fügen Sie vor der Telefonnummer die AT-Ländervorwahl +43 ein',
        },
        {
          countryCode: 'IE',
          placeholder: '+353 00 000 0000',
          helpText: 'Include the IE country code +353 before the phone number',
        },
        {
          countryCode: 'IT',
          placeholder: '+39 000 000 0000',
          helpText: 'Includere il prefisso internazionale IT +39 prima del numero di telefono',
        },
        {
          countryCode: 'NO',
          placeholder: '+47 000 00 000',
          helpText: 'Inkluder NO landskode +47 før telefonnummeret',
        },
        {
          countryCode: 'SE',
          placeholder: '+46 00 000 00 00',
          helpText: 'Inkludera SE landskod +46 före telefonnumret',
        },
        {
          countryCode: 'DK',
          placeholder: '+45 00 00 00 00',
          helpText: 'Inkluder DK landekode +45 før telefonnummeret',
        },
        {
          countryCode: 'FI',
          placeholder: '+358 00 000 0000',
          helpText: 'Sisällytä FI-maakoodi +358 ennen puhelinnumeroa',
        },
        {
          countryCode: 'EE',
          placeholder: '+372 0000 0000',
          helpText: 'Lisage EE riigikood +372 telefoninumbri ette',
        },
        {
          countryCode: 'PL',
          placeholder: '+48 000 000 000',
          helpText: 'Podaj numer kierunkowy PL +48 przed numerem telefonu',
        },
        {
          countryCode: 'SK',
          placeholder: '+421 000 000 000',
          helpText: 'Pred telefónne číslo uveďte kód krajiny SK +421',
        },
        {
          countryCode: 'LV',
          placeholder: '+371 0000 0000',
          helpText: 'Iekļaujiet LV valsts kodu +371 pirms tālruņa numura',
        },
        {
          countryCode: 'LT',
          placeholder: '+370 0000 0000',
          helpText: 'Įtraukite LT šalies kodą +370 prieš telefono numerį',
        },
        {
          countryCode: 'GR',
          placeholder: '+30 000 000 0000',
          helpText: 'Συμπεριλάβετε τον κωδικό χώρας GR +30 πριν από τον αριθμό τηλεφώνου',
        },
        {
          countryCode: 'PT',
          placeholder: '+351 000 000 000',
          helpText: 'Inclua o código de país PT +351 antes do número de telefone',
        },
        {
          countryCode: 'HR',
          placeholder: '+385 00 000 0000',
          helpText: 'Uključite HR pozivni broj države +385 prije telefonskog broja',
        },
        {
          countryCode: 'SI',
          placeholder: '+386 00 000 000',
          helpText: 'Vključite SI kodo države +386 pred telefonsko številko',
        },
        {
          countryCode: 'IS',
          placeholder: '+354 000 0000',
          helpText: 'Láttu IS landsnúmer +354 fylgja á undan símanúmerinu',
        },
        {
          countryCode: 'LU',
          placeholder: '+352 000 000 000',
          helpText: 'Incluez le code pays LU +352 avant le numéro de téléphone',
        },
        {
          countryCode: 'MC',
          placeholder: '+377 00 00 00 00',
          helpText: 'Incluez le code pays MC +377 avant le numéro de téléphone',
        },
        {
          countryCode: 'AD',
          placeholder: '+376 000 000',
          helpText: 'Incloeu el codi de país AD +376 abans del número de telèfon',
        },
        {
          countryCode: 'JE',
          placeholder: '+44 0000 000000',
          helpText: 'Include the JE country code +44 before the phone number',
        },
        {
          countryCode: 'IM',
          placeholder: '+44 0000 000000',
          helpText: 'Include the IM country code +44 before the phone number',
        },
        {
          countryCode: 'GG',
          placeholder: '+44 0000 000000',
          helpText: 'Include the GG country code +44 before the phone number',
        },
        {
          countryCode: 'AL',
          placeholder: '+355 00 000 0000',
          helpText: 'Përfshini kodin e vendit AL +355 para numrit të telefonit',
        },
        {
          countryCode: 'SM',
          placeholder: '+378 0000 000000',
          helpText: 'Includere il prefisso internazionale SM +378 prima del numero di telefono',
        },
        {
          countryCode: 'FO',
          placeholder: '+298 000000',
          helpText: 'Inkluder FO landekode +298 før telefonnummeret',
        },
        {
          countryCode: 'MT',
          placeholder: '+356 0000 0000',
          helpText: 'Include the MT country code +356 before the phone number',
        },
        {
          countryCode: 'LI',
          placeholder: '+423 000 0000',
          helpText: 'Fügen Sie vor der Telefonnummer die LI-Ländervorwahl +423 ein',
        },
        {
          countryCode: 'GI',
          placeholder: '+350 000 00000',
          helpText: 'Include the GI country code +350 before the phone number',
        },
        {
          countryCode: 'MD',
          placeholder: '+373 00 000 000',
          helpText: 'Includeți codul de țară MD +373 înaintea numărului de telefon',
        },
        {
          countryCode: 'HU',
          placeholder: '+36 00 000 0000',
          helpText: 'A telefonszám előtt adja meg a HU országkódot +36',
        },
        {
          countryCode: 'NZ',
          placeholder: '+64 00 000 0000',
          helpText: 'Include the NZ country code +64 before the phone number',
        },
        {
          countryCode: 'ME',
          placeholder: '+382 00 000 000',
          helpText: 'Uključite ME pozivni broj države +382 prije telefonskog broja',
        },
      ];
      
      if (!countryCode || typeof countryCode !== 'string') {
        return mockPlaceholders[0].helpText;
      }
      
      const selectedHelpText = mockPlaceholders.find(function(item) {
          return item && item.countryCode === countryCode;
        });
        
        return selectedHelpText ? selectedHelpText.helpText : mockPlaceholders[0].helpText;
    }

    function setDefaultHelpText(countryCode) {
      const helpTextSpan = document.querySelector('#help-text');
      if (!helpTextSpan) {
        return;
      }

        
    }

    function updateHelpTextCountryCode(countryCode, fieldName) {
      if (!countryCode || !fieldName) {
        return;
      }
      
      setDefaultHelpText(countryCode);
    }

    function initializeSmsPhoneDropdown(fieldName) {
      if (!fieldName || typeof fieldName !== 'string') {
        return;
      }
      
      const dropdown = document.querySelector('#country-select-' + fieldName);
      const displayFlag = document.querySelector('#flag-display-' + fieldName);
      
      if (!dropdown || !displayFlag) {
        return;
      }

      const smsPhoneData = window.MC?.smsPhoneData;
      if (smsPhoneData && smsPhoneData.programs && Array.isArray(smsPhoneData.programs)) {
        dropdown.innerHTML = generateDropdownOptions(smsPhoneData.programs);
      }

      const defaultProgram = getDefaultCountryProgram(smsPhoneData?.defaultCountryCode, smsPhoneData?.programs);
      if (defaultProgram && defaultProgram.countryCode) {
        dropdown.value = defaultProgram.countryCode;
        
        const flagSpan = displayFlag?.querySelector('#flag-emoji-' + fieldName);
        if (flagSpan) {
          flagSpan.textContent = getCountryUnicodeFlag(defaultProgram.countryCode);
          flagSpan.setAttribute('aria-label', sanitizeHtml(defaultProgram.countryCode) + ' flag');
        }
        
        updateSmsLegalText(defaultProgram.countryCode, fieldName);
        updatePlaceholder(defaultProgram.countryCode, fieldName);
        updateCountryCodeInstruction(defaultProgram.countryCode, fieldName);
      }

     
      var smsNotRequiredRemoveCountryCodeEnabled = true;
      var smsField = Object.values({"EMAIL":{"name":"EMAIL","label":"E-Mail-Adresse","helper_text":"","type":"email","required":true,"audience_field_name":"E-Mail-Adresse","merge_id":0,"help_text_enabled":false,"enabled":true,"order":0,"field_type":"merge"},"FNAME":{"name":"FNAME","label":"Vorname","helper_text":"","type":"text","required":false,"audience_field_name":"Vorname","merge_id":1,"help_text_enabled":false,"enabled":true,"order":1,"field_type":"merge"},"LNAME":{"name":"LNAME","label":"Nachname","helper_text":"","type":"text","required":false,"audience_field_name":"Nachname","merge_id":2,"help_text_enabled":false,"enabled":true,"order":2,"field_type":"merge"},"ADDRESS":{"name":"ADDRESS","label":"Adresse","helper_text":"","type":"address","required":false,"audience_field_name":"Adresse","enabled":false,"order":null,"field_type":"merge","merge_id":3,"countries":{"2":"Albania","3":"Algeria","4":"Andorra","5":"Angola","6":"Argentina","7":"Armenia","8":"Australia","9":"Austria","10":"Azerbaijan","11":"Bahamas","12":"Bahrain","13":"Bangladesh","14":"Barbados","15":"Belarus","16":"Belgium","17":"Belize","18":"Benin","19":"Bermuda","20":"Bhutan","21":"Bolivia","22":"Bosnia and Herzegovina","23":"Botswana","24":"Brazil","25":"Bulgaria","26":"Burkina Faso","27":"Burundi","28":"Cambodia","29":"Cameroon","30":"Canada","31":"Cape Verde","32":"Cayman Islands","33":"Central African Republic","34":"Chad","35":"Chile","36":"China","37":"Colombia","38":"Congo","40":"Croatia","41":"Cyprus","42":"Czech Republic","43":"Denmark","44":"Djibouti","45":"Ecuador","46":"Egypt","47":"El Salvador","48":"Equatorial Guinea","49":"Eritrea","50":"Estonia","51":"Ethiopia","52":"Fiji","53":"Finland","54":"France","56":"Gabon","57":"Gambia","58":"Georgia","59":"Germany","60":"Ghana","61":"Greece","62":"Guam","63":"Guinea","64":"Guinea-Bissau","65":"Guyana","66":"Honduras","67":"Hong Kong","68":"Hungary","69":"Iceland","70":"India","71":"Indonesia","74":"Ireland","75":"Israel","76":"Italy","78":"Japan","79":"Jordan","80":"Kazakhstan","81":"Kenya","82":"Kuwait","83":"Kyrgyzstan","84":"Lao People's Democratic Republic","85":"Latvia","86":"Lebanon","87":"Lesotho","88":"Liberia","90":"Liechtenstein","91":"Lithuania","92":"Luxembourg","93":"Macedonia","94":"Madagascar","95":"Malawi","96":"Malaysia","97":"Maldives","98":"Mali","99":"Malta","100":"Mauritania","101":"Mexico","102":"Moldova","103":"Monaco","104":"Mongolia","105":"Morocco","106":"Mozambique","107":"Namibia","108":"Nepal","109":"Netherlands","110":"Netherlands Antilles","111":"New Zealand","112":"Nicaragua","113":"Niger","114":"Nigeria","116":"Norway","117":"Oman","118":"Pakistan","119":"Panama","120":"Paraguay","121":"Peru","122":"Philippines","123":"Poland","124":"Portugal","126":"Qatar","127":"Reunion","128":"Romania","129":"Russia","130":"Rwanda","132":"Samoa (Independent)","133":"Saudi Arabia","134":"Senegal","135":"Seychelles","136":"Sierra Leone","137":"Singapore","138":"Slovakia","139":"Slovenia","140":"Somalia","141":"South Africa","142":"South Korea","143":"Spain","144":"Sri Lanka","146":"Suriname","147":"Swaziland","148":"Sweden","149":"Switzerland","152":"Taiwan","153":"Tanzania","154":"Thailand","155":"Togo","156":"Tunisia","157":"Turkiye","158":"Turkmenistan","159":"Uganda","161":"Ukraine","162":"United Arab Emirates","163":"Uruguay","164":"USA","165":"Uzbekistan","166":"Vatican City State (Holy See)","167":"Venezuela","168":"Vietnam","169":"Virgin Islands (British)","170":"Yemen","173":"Zambia","174":"Zimbabwe","175":"Antigua And Barbuda","176":"Anguilla","178":"American Samoa","179":"Aruba","180":"Brunei Darussalam","181":"Bouvet Island","183":"Cook Islands","185":"Christmas Island","187":"Dominican Republic","188":"Western Sahara","189":"Falkland Islands","191":"Faroe Islands","192":"Grenada","193":"French Guiana","194":"Gibraltar","195":"Greenland","196":"Guadeloupe","198":"Guatemala","200":"Haiti","202":"Jamaica","203":"Kiribati","204":"Comoros","205":"Saint Kitts and Nevis","206":"Saint Lucia","207":"Marshall Islands","208":"Macau","210":"Martinique","212":"Mauritius","213":"New Caledonia","214":"Norfolk Island","215":"Nauru","217":"Niue","219":"Papua New Guinea","221":"Pitcairn","222":"Palau","223":"Solomon Islands","225":"Svalbard and Jan Mayen Islands","227":"San Marino","232":"Tonga","233":"Timor-Leste","234":"Trinidad and Tobago","235":"Tuvalu","237":"Saint Vincent and the Grenadines","238":"Virgin Islands (U.S.)","239":"Vanuatu","241":"Mayotte","242":"Myanmar","255":"Sao Tome and Principe","257":"South Georgia and the South Sandwich Islands","260":"Tajikistan","262":"United Kingdom","268":"Costa Rica","270":"Guernsey","272":"North Korea","274":"Afghanistan","275":"Cote D'Ivoire","276":"Cuba","277":"French Polynesia","278":"Iran","279":"Iraq","281":"Libya","282":"Palestine","285":"Syria","286":"Aaland Islands","287":"Turks & Caicos Islands","288":"Jersey  (Channel Islands)","289":"Dominica","290":"Montenegro","293":"Sudan","294":"Montserrat","298":"Curacao","302":"Sint Maarten","311":"South Sudan","315":"Republic of Kosovo","318":"Congo, Democratic Republic of the","323":"Isle of Man","324":"Saint Martin","325":"Bonaire, Saint Eustatius and Saba","326":"Serbia"},"defaultcountry":164},"PHONE":{"name":"PHONE","label":"Telefonnummer","helper_text":"","type":"phone","required":false,"audience_field_name":"Telefonnummer","phoneformat":"","enabled":false,"order":null,"field_type":"merge","merge_id":4},"COMPANY":{"name":"COMPANY","label":"Company","helper_text":"","type":"text","required":false,"audience_field_name":"Company","enabled":false,"order":null,"field_type":"merge","merge_id":6}}).find(function(f) { return f.name === fieldName && f.type === 'smsphone'; });
      var isRequired = smsField ? smsField.required : false;
      var shouldAppendCountryCode = smsNotRequiredRemoveCountryCodeEnabled ? isRequired : true;
      
      var phoneInput = document.querySelector('#mce-' + fieldName);
      if (phoneInput && defaultProgram.countryCallingCode && shouldAppendCountryCode) {
        phoneInput.value = defaultProgram.countryCallingCode;
      }
      


      displayFlag?.addEventListener('click', function(e) {
        dropdown.focus();
      });


      dropdown?.addEventListener('change', function() {
        const selectedCountry = this.value;
        
        if (!selectedCountry || typeof selectedCountry !== 'string') {
          return;
        }
        
        const flagSpan = displayFlag?.querySelector('#flag-emoji-' + fieldName);
        if (flagSpan) {
          flagSpan.textContent = getCountryUnicodeFlag(selectedCountry);
          flagSpan.setAttribute('aria-label', sanitizeHtml(selectedCountry) + ' flag');
        }

         
        const selectedProgram = window.MC?.smsPhoneData?.programs.find(function(program) {
          return program && program.countryCode === selectedCountry;
        });

        var smsNotRequiredRemoveCountryCodeEnabled = true;
        var smsField = Object.values({"EMAIL":{"name":"EMAIL","label":"E-Mail-Adresse","helper_text":"","type":"email","required":true,"audience_field_name":"E-Mail-Adresse","merge_id":0,"help_text_enabled":false,"enabled":true,"order":0,"field_type":"merge"},"FNAME":{"name":"FNAME","label":"Vorname","helper_text":"","type":"text","required":false,"audience_field_name":"Vorname","merge_id":1,"help_text_enabled":false,"enabled":true,"order":1,"field_type":"merge"},"LNAME":{"name":"LNAME","label":"Nachname","helper_text":"","type":"text","required":false,"audience_field_name":"Nachname","merge_id":2,"help_text_enabled":false,"enabled":true,"order":2,"field_type":"merge"},"ADDRESS":{"name":"ADDRESS","label":"Adresse","helper_text":"","type":"address","required":false,"audience_field_name":"Adresse","enabled":false,"order":null,"field_type":"merge","merge_id":3,"countries":{"2":"Albania","3":"Algeria","4":"Andorra","5":"Angola","6":"Argentina","7":"Armenia","8":"Australia","9":"Austria","10":"Azerbaijan","11":"Bahamas","12":"Bahrain","13":"Bangladesh","14":"Barbados","15":"Belarus","16":"Belgium","17":"Belize","18":"Benin","19":"Bermuda","20":"Bhutan","21":"Bolivia","22":"Bosnia and Herzegovina","23":"Botswana","24":"Brazil","25":"Bulgaria","26":"Burkina Faso","27":"Burundi","28":"Cambodia","29":"Cameroon","30":"Canada","31":"Cape Verde","32":"Cayman Islands","33":"Central African Republic","34":"Chad","35":"Chile","36":"China","37":"Colombia","38":"Congo","40":"Croatia","41":"Cyprus","42":"Czech Republic","43":"Denmark","44":"Djibouti","45":"Ecuador","46":"Egypt","47":"El Salvador","48":"Equatorial Guinea","49":"Eritrea","50":"Estonia","51":"Ethiopia","52":"Fiji","53":"Finland","54":"France","56":"Gabon","57":"Gambia","58":"Georgia","59":"Germany","60":"Ghana","61":"Greece","62":"Guam","63":"Guinea","64":"Guinea-Bissau","65":"Guyana","66":"Honduras","67":"Hong Kong","68":"Hungary","69":"Iceland","70":"India","71":"Indonesia","74":"Ireland","75":"Israel","76":"Italy","78":"Japan","79":"Jordan","80":"Kazakhstan","81":"Kenya","82":"Kuwait","83":"Kyrgyzstan","84":"Lao People's Democratic Republic","85":"Latvia","86":"Lebanon","87":"Lesotho","88":"Liberia","90":"Liechtenstein","91":"Lithuania","92":"Luxembourg","93":"Macedonia","94":"Madagascar","95":"Malawi","96":"Malaysia","97":"Maldives","98":"Mali","99":"Malta","100":"Mauritania","101":"Mexico","102":"Moldova","103":"Monaco","104":"Mongolia","105":"Morocco","106":"Mozambique","107":"Namibia","108":"Nepal","109":"Netherlands","110":"Netherlands Antilles","111":"New Zealand","112":"Nicaragua","113":"Niger","114":"Nigeria","116":"Norway","117":"Oman","118":"Pakistan","119":"Panama","120":"Paraguay","121":"Peru","122":"Philippines","123":"Poland","124":"Portugal","126":"Qatar","127":"Reunion","128":"Romania","129":"Russia","130":"Rwanda","132":"Samoa (Independent)","133":"Saudi Arabia","134":"Senegal","135":"Seychelles","136":"Sierra Leone","137":"Singapore","138":"Slovakia","139":"Slovenia","140":"Somalia","141":"South Africa","142":"South Korea","143":"Spain","144":"Sri Lanka","146":"Suriname","147":"Swaziland","148":"Sweden","149":"Switzerland","152":"Taiwan","153":"Tanzania","154":"Thailand","155":"Togo","156":"Tunisia","157":"Turkiye","158":"Turkmenistan","159":"Uganda","161":"Ukraine","162":"United Arab Emirates","163":"Uruguay","164":"USA","165":"Uzbekistan","166":"Vatican City State (Holy See)","167":"Venezuela","168":"Vietnam","169":"Virgin Islands (British)","170":"Yemen","173":"Zambia","174":"Zimbabwe","175":"Antigua And Barbuda","176":"Anguilla","178":"American Samoa","179":"Aruba","180":"Brunei Darussalam","181":"Bouvet Island","183":"Cook Islands","185":"Christmas Island","187":"Dominican Republic","188":"Western Sahara","189":"Falkland Islands","191":"Faroe Islands","192":"Grenada","193":"French Guiana","194":"Gibraltar","195":"Greenland","196":"Guadeloupe","198":"Guatemala","200":"Haiti","202":"Jamaica","203":"Kiribati","204":"Comoros","205":"Saint Kitts and Nevis","206":"Saint Lucia","207":"Marshall Islands","208":"Macau","210":"Martinique","212":"Mauritius","213":"New Caledonia","214":"Norfolk Island","215":"Nauru","217":"Niue","219":"Papua New Guinea","221":"Pitcairn","222":"Palau","223":"Solomon Islands","225":"Svalbard and Jan Mayen Islands","227":"San Marino","232":"Tonga","233":"Timor-Leste","234":"Trinidad and Tobago","235":"Tuvalu","237":"Saint Vincent and the Grenadines","238":"Virgin Islands (U.S.)","239":"Vanuatu","241":"Mayotte","242":"Myanmar","255":"Sao Tome and Principe","257":"South Georgia and the South Sandwich Islands","260":"Tajikistan","262":"United Kingdom","268":"Costa Rica","270":"Guernsey","272":"North Korea","274":"Afghanistan","275":"Cote D'Ivoire","276":"Cuba","277":"French Polynesia","278":"Iran","279":"Iraq","281":"Libya","282":"Palestine","285":"Syria","286":"Aaland Islands","287":"Turks & Caicos Islands","288":"Jersey  (Channel Islands)","289":"Dominica","290":"Montenegro","293":"Sudan","294":"Montserrat","298":"Curacao","302":"Sint Maarten","311":"South Sudan","315":"Republic of Kosovo","318":"Congo, Democratic Republic of the","323":"Isle of Man","324":"Saint Martin","325":"Bonaire, Saint Eustatius and Saba","326":"Serbia"},"defaultcountry":164},"PHONE":{"name":"PHONE","label":"Telefonnummer","helper_text":"","type":"phone","required":false,"audience_field_name":"Telefonnummer","phoneformat":"","enabled":false,"order":null,"field_type":"merge","merge_id":4},"COMPANY":{"name":"COMPANY","label":"Company","helper_text":"","type":"text","required":false,"audience_field_name":"Company","enabled":false,"order":null,"field_type":"merge","merge_id":6}}).find(function(f) { return f.name === fieldName && f.type === 'smsphone'; });
        var isRequired = smsField ? smsField.required : false;
        var shouldAppendCountryCode = smsNotRequiredRemoveCountryCodeEnabled ? isRequired : true;
        
        var phoneInput = document.querySelector('#mce-' + fieldName);
        if (phoneInput && selectedProgram.countryCallingCode && shouldAppendCountryCode) {
          phoneInput.value = selectedProgram.countryCallingCode;
        }
        
        
        updateSmsLegalText(selectedCountry, fieldName);
        updatePlaceholder(selectedCountry, fieldName);
        updateCountryCodeInstruction(selectedCountry, fieldName);
      });
    }

    document.addEventListener('DOMContentLoaded', function() {
      const smsPhoneFields = document.querySelectorAll('[id^="country-select-"]');
      
      smsPhoneFields.forEach(function(dropdown) {
        const fieldName = dropdown?.id.replace('country-select-', '');
        initializeSmsPhoneDropdown(fieldName);
      });
    });