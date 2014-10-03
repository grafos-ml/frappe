/**
 * Created by joaonrb on 2/20/14.
 */

var ICONS_PER_PAGE = 4;
var NUMBER_OF_RECOMMENDATIONS = 16;

function loadRecommendations(user) {
    uri = "/api/v2/recommend/32/"+user+".json";
    $.getJSON(uri, function(data) {
        var items = [];
        $.each(data.recommendations, function(index) {
            $.getJSON("/api/v2/item/"+data.recommendations[index]+".json?user="+user+"&rank="+(index+1),
                function(elem_data) {
                    elem_data.installation_date = data.recommendations[index].acquisition_date;
                    elem_data.removed_date = data.recommendations[index].dropped_date;
                    elem_data.install_or_remove = "plus";
                    elem_data.install_or_remove_color = "success";
                    elem_data.action = "item_acquire('"+user+"','"+elem_data.external_id+"');";
                    elem_data.index = index+1;
                    items.push(elem_data);
                    if(data.recommendations.length == index+1) {
                        window.setTimeout(function () {
                            var html = appContainer({"apps": items});
                            $("#recommendedApps").html(html);
                            loadLargeIcons();
                        }, 1000);
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

USERLIST = "/users/";
USERITEMS = "user-items/";
USERRECOMMEND = "recommend/"

angular.module("frappeApp", ["ngRoute"])
    .controller("FrappeController", ["$scope", function($scope) {

        $scope.loadUsers = function() {
            window.location.replace("#/url/" + $scope.frappeText +"");
        };
    }])
    .config(["$routeProvider",
        function($routeProvider) {
            $routeProvider.when("/url/:frappeURL*", {
                templateUrl: "templates/list.html",
                controller: function ($scope, $http, $routeParams) {
                    $http({method: "GET", url: $routeParams.frappeURL + USERLIST})
                        .success(function(data, status) {
                            $scope.users = data;
                            $scope.url = $routeParams.frappeURL;
                            $.each(data, function(i, user){
                                $http({method: "GET", url: $routeParams.frappeURL.concat("/", USERITEMS, user.external_id, "/")})
                                    .success(function(data, status) {
                                        $scope.users[i].number_of_items = data.items.length;
                                    })
                            });
                        })
                }
            }).when("/:user/url/:frappeURL*", {
                templateUrl: "./templates/user.html",
                controller: function ($scope, $http, $routeParams) {
                        $http({method: "GET", url: $routeParams.frappeURL.concat(USERITEMS, $routeParams.user, "/")})
                            .success(function (data, status) {
                                $scope.all_items = data.items;
                                $scope.from = 0;
                                $scope.to  = ICONS_PER_PAGE;
                                $scope.current_page = 1;
                                $scope.pages = [];
                                for(var i=0; (i*ICONS_PER_PAGE) < data.items.length; i++) {
                                    $scope.pages.push(i+1);
                                }
                                $scope.user = data.user;
                                $scope.url = $routeParams.frappeURL;
                                $.each(data.items, function (i, item) {
                                    $http({method: "GET", url: "https://marketplace.firefox.com/api/v2/apps/app/".concat(item.external_id, "/")})
                                        .success(function (data, status) {
                                            $scope.all_items[i].details = data;
                                            $scope.all_items[i].index = i+1;
                                        })
                                });
                            });
                        $scope.reloadRecommended = function(user) {
                            $scope.recommended = [];
                            $http({method: "GET", url: $routeParams.frappeURL.concat(USERRECOMMEND, NUMBER_OF_RECOMMENDATIONS, "/", user, "/")})
                                .success(function (data, status) {
                                    $.each(data.recommendations, function (i, item) {
                                        $scope.recommended.push({"external_id": item, "index": i + 1})
                                        $http({method: "GET", url: "https://marketplace.firefox.com/api/v2/apps/app/".concat(item, "/")})
                                            .success(function (data, status) {
                                                $scope.recommended[i].details = data;
                                            })
                                    });
                                });
                        };
                        $scope.change_page_to = function(page) {
                            if((page-1) in $scope.pages) {
                                $scope.from = (page-1) * ICONS_PER_PAGE;
                                $scope.to  = page * ICONS_PER_PAGE;
                                $scope.current_page = page;
                            }
                        }
                        $scope.reloadRecommended($routeParams.user);
                    }

            }).otherwise({
                redirectTo: '/'
            });
            // configure html5 to get links working on jsfiddle
            //$locationProvider.html5Mode(true);
        }
    ]);