/**
 * Created by joaonrb on 2/20/14.
 */

var ICONS_PER_PAGE = 4;
var NUMBER_OF_RECOMMENDATIONS = 16;

USERLIST = "/users/";
USERITEMS = "user-items/";
USERRECOMMEND = "recommend/"

angular.module("frappeApp", ["ngRoute"])
    .controller("FrappeController", ["$scope", function($scope) {

        $scope.loadUsers = function() {
            window.location.replace("#/page/1/url/" + $scope.frappeText);
        };
    }])
    .config(["$routeProvider",
        function($routeProvider) {
            $routeProvider.when("/page/:page/url/:frappeURL*", {
                templateUrl: "templates/list.html",
                controller: function ($scope, $http, $routeParams) {
                    $http({method: "GET", url: $routeParams.frappeURL.concat(USERLIST, "?users=15", "&offset=", (($routeParams.page-1)*15).toString())})
                        .success(function(data, status) {
                            $scope.users = data;
                            $scope.url = $routeParams.frappeURL;
                            $scope.page = parseInt($routeParams.page);
                            $.each(data, function(i, user){
                                $http({method: "GET", url: $routeParams.frappeURL.concat("/", USERITEMS, user.external_id, "/")})
                                    .success(function(data, status) {
                                        $scope.users[i].number_of_items = data.items.length;
                                    })
                            });
                        })
                }
            }).when("/user/:user/url/:frappeURL*", {
                templateUrl: "./templates/user.html",
                controller: function ($scope, $http, $routeParams) {
                        $scope.user = $routeParams.user;
                        $scope.url = $routeParams.frappeURL;
                        $scope.reloadOwned = function(user) {
                            $http({method: "GET", url: $routeParams.frappeURL.concat(USERITEMS, user, "/")})
                                .success(function (data, status) {
                                    $scope.owned_items = data.items.filter(function(elem){
                                        return !elem.is_dropped;
                                    });
                                    $scope.all_items = data.items;
                                    $scope.from = 0;
                                    $scope.to  = ICONS_PER_PAGE;
                                    $scope.current_page = 1;
                                    $scope.pages = [];
                                    for(var i=0; (i*ICONS_PER_PAGE) < $scope.owned_items.length; i++) {
                                        $scope.pages.push(i+1);
                                    }
                                    $.each($scope.owned_items, function (i, item) {
                                        $http({method: "GET", url: "https://marketplace.firefox.com/api/v2/apps/app/".concat(item.external_id, "/")})
                                            .success(function (data, status) {
                                                $scope.owned_items[i].details = data;
                                                $scope.owned_items[i].index = i+1;
                                            })
                                    });
                                });
                        };
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
                        };
                        $scope.item_remove = function(user, item) {
                            uri = $routeParams.frappeURL+"user-items/"+user+"/";
                            $.ajax({
                                url: uri,
                                type: "DELETE",
                                data: {"item_to_remove": item}
                            }).done(function(data) {
                                    window.location.reload()
                                }
                            ).fail(function(data){
                                    $(window.open().document.body).html(data.responseText);
                                });
                        };
                        $scope.item_acquire = function(user, item) {
                            uri = $routeParams.frappeURL+"user-items/"+user+"/";
                            $.ajax({
                                url: uri,
                                type: "POST",
                                data: {item_to_acquire: item}
                            }).done(
                                function(data) {
                                    window.location.reload()
                                }
                            ).fail(function(data){
                                    $(window.open().document.body).html(data.responseText);
                                });
                        };
                        $scope.reloadOwned($routeParams.user);
                        $scope.reloadRecommended($routeParams.user);

                    }

            }).otherwise({
                redirectTo: '/'
            });
            // configure html5 to get links working on jsfiddle
            //$locationProvider.html5Mode(true);
        }
    ]);