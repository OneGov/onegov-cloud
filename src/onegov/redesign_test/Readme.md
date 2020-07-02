# Foundation6 TestApp

Included in here, a copy of the bootstrap html showcasing various elements. You can essentially check visually,
if all styles are correctly applied.  

Launch a new bootstrap project by

    echo sample-project | foundation new --framework sites --template zurb
    yarn start
    
Compare the results with:

    http://127.0.0.1:8080/onegov_redesign_test/

This app also shows how to integrate foundation6. Just inherit from `FoundatioApp` instead of `Framework` 
and inherit from `FoundationLayout` instead of `ChameleonLayout`.
