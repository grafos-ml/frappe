/**
 * Created by joaonrb on 3/6/14.
 */
/*
  Set elements based
 */


function loadIcons(name, size) {
    var ids = $(".ff-"+name+"-icon");
    $.each(ids, function(index){
        var item_id = ids[index].id;
        if($("#"+item_id).attr("src") === null || $("#"+item_id).attr("src") === "") {
            alert(item_id);
            $.getJSON("/api/v2/item/"+item_id+"/", function(data) {
                $.getJSON(data.details, function(item) {
                    $("#"+item_id+".ff-"+name+"-icon").attr("src", item.icons[size]);
                });
            });
        }
    });
}

function loadSmallIcons() {
    loadIcons("small", 16);
}

function loadStandardIcons() {
    loadIcons("std", 64);
}

function loadLargeIcons() {
    loadIcons("large", 128);
}

$(function() {
    loadSmallIcons();
});