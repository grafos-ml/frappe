/**
 * Created by joaonrb on 2/20/14.
 */

var perPage = 4;

function goTo(page, pager, listElement){
    if(page >= 0 && page < listElement.children().size()/perPage) {
        var startAt = page * perPage, endOn = startAt + perPage;
        listElement.children().css('display','none').slice(startAt, endOn).css('display','block');
        $(pager).data("curr",page);
    }
}

function Paginator(container, paginator) {
    this.constructor = function(container, paginator) {
        this.listElement = $(container);
        this.numItems = this.listElement.children().size();
        this.paginator = paginator;
        this.numPages = Math.ceil(this.numItems/perPage);
        $(this.paginator).data("curr",0);
        this.curr = 0;
        this.buildPaginator();
        $(this.paginator+' .page_link:first').addClass('active');
        this.listElement.children().css('display', 'none');
        this.listElement.children().slice(0,perPage).css('display','block');

        $(this.paginator+' li .page_link').click(function() {
            var clickedPage = $(this).html().valueOf() - 1;
            goTo(clickedPage, paginator, $(container), perPage);
        });

        $(this.paginator+' .page_prev').click(this.previous);
        $(this.paginator+' .page_next').click(this.next);
    }

    this.previous = function() {
        var goToPage = parseInt($(paginator).data("curr")) - 1;
        goTo(goToPage, paginator, $(container));
    }

    this.next = function() {
        var goToPage = parseInt($(paginator).data("curr")) + 1;
        goTo(goToPage,paginator,$(container));
    }


    this.constructor(container,paginator);
}

Paginator.prototype.buildPaginator = function() {
    $(this.paginator).html(" ");
    $('<li><a href="#" class="page_prev">&laquo;</a></li>').appendTo(this.paginator);
    while(this.numPages > this.curr)
        $('<li><a href="#" class="page_link">' + (++this.curr) + '</a></li>').appendTo(this.paginator);
    $('<li><a href="#" class="page_next">&raquo;</a></li>').appendTo(this.paginator);
}

function getInstalledAppsURI(user, items, offset) {
    uri = "/api/v2/user-items/" + user +".json";
    extra_parameters = [];
    if(typeof items == "number")
        extra_parameters.push("items="+items);
    if(typeof offset == "number")
        extra_parameters.push("offset=" + offset);
    if(extra_parameters.length != 0)
        uri = uri + "?" + extra_parameters.join("&");
    return uri;
}

function loadInstalledApps(user) {
    uri = getInstalledAppsURI(user);
    $.getJSON(uri, function(data) {
        var items = [];
        alert(JSON.stringify(data));
        $.each(data.items, function(index) {
            $.getJSON("/api/v2/item/"+data.items[index].external_id+".json?user="+user, function(elem_data) {
                if(data.items[index].removed_date == null) {
                    elem_data.installation_date = data.items[index].acquisition_date;
                    elem_data.install_or_remove = "minus";
                    elem_data.install_or_remove_color = "danger";
                    elem_data.action = "item_remove('"+user+"','"+elem_data.external_id+"');";
                    items.push(elem_data);
                    if(data.items.length == index+1) {
                        window.setTimeout(function () {
                            var html = appContainer({"apps": items});
                            $("#installedApps").html(html);
                            loadLargeIcons();
                            new Paginator('#installedApps','#installedPager');
                        }, 500);
                    }
                }
            });
        });
    });
}

function loadRecommendations(user) {
    uri = "/api/v2/recommend/4/"+user+".json";
    $.getJSON(uri, function(data) {
        var items = [];
        $.each(data.recommendations, function(index) {
            $.getJSON("/api/v2/item/"+data.recommendations[index]+".json?user="+user+"&rank="+(index+1),
                function(elem_data) {
                elem_data.installation_date = data.recommendations[index].acquisition_date;
                elem_data.removed_date = data.recommendations[index].dropped_date;
                elem_data.install_or_remove = "plus";
                elem_data.install_or_remove_color = "success";
                elem_data.action = "item_acquire('"+user+"','"+elem_data.external_id+"');"
                items.push(elem_data);
                if(data.recommendations.length == index+1) {
                    window.setTimeout(function () {
                        var html = appContainer({"apps": items});
                        $("#recommendedApps").html(html);
                        loadLargeIcons();
                    },1000);
                }
            });
        });
    });
}

function item_remove(user, item) {
    uri = "/api/v2/user-items/"+user+"/";
    $.ajax({
        url: uri,
        type: "DELETE",
        data: {"item_to_remove": item}
    }).done(function(data) {
            loadInstalledApps(user);
            loadRecommendations(user);
        }
    ).fail(function(data){
        $(window.open().document.body).html(data.responseText);
    });
}

function item_acquire(user, item) {
    uri = "/api/v2/user-items/"+user+"/";
    $.post(uri, {"item_to_acquire": item}).done(
        function(data) {
            loadInstalledApps(user);
            loadRecommendations(user);
        }
    ).fail(function(data){
        $(window.open().document.body).html(data.responseText);
    });
}