$(document).ready(function(){
    $("#person_choices").chosen().change(function (event) {
        var person_info = $(event.target).val();
        
        console.log('Zusammen:', person_info);
        separated_values = person_info.split(', ');
        for (const info of separated_values) {
            console.log(info)
        }
        document.getElementById(
            'person_name').value=separated_values[0]
        document.getElementById(
            'person_function').value=separated_values[1]
        document.getElementById(
            'person_political_affiliation').value=separated_values[2]
        document.getElementById(
            'person_place').value=separated_values[3]
        document.getElementById(
            'person_picture').value=separated_values[4]
    });
})
