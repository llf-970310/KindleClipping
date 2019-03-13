/**
 * demo.js
 * http://www.codrops.com
 *
 * Licensed under the MIT license.
 * http://www.opensource.org/licenses/mit-license.php
 *
 * Copyright 2016, Codrops
 * http://www.codrops.com
 */
;(function (window) {

    'use strict';

    // taken from mo.js demos
    function isIOSSafari() {
        var userAgent;
        userAgent = window.navigator.userAgent;
        return userAgent.match(/iPad/i) || userAgent.match(/iPhone/i);
    };

    // taken from mo.js demos
    function isTouch() {
        var isIETouch;
        isIETouch = navigator.maxTouchPoints > 0 || navigator.msMaxTouchPoints > 0;
        return [].indexOf.call(window, 'ontouchstart') >= 0 || isIETouch;
    };

    // taken from mo.js demos
    var isIOS = isIOSSafari(),
        clickHandler = isIOS || isTouch() ? 'touchstart' : 'click';

    function extend(a, b) {
        for (var key in b) {
            if (b.hasOwnProperty(key)) {
                a[key] = b[key];
            }
        }
        return a;
    }

    function Animocon(el, options) {
        this.el = el;
        this.options = extend({}, this.options);
        extend(this.options, options);

        if (el.className.indexOf("checked") != -1)
            this.checked = true;
        else
            this.checked = false;

        this.timeline = new mojs.Timeline();

        for (var i = 0, len = this.options.tweens.length; i < len; ++i) {
            this.timeline.add(this.options.tweens[i]);
        }

        var self = this;
        this.el.addEventListener(clickHandler, function () {
            if (self.checked) {
                self.options.onUnCheck();
            }
            else {
                self.options.onCheck();
                self.timeline.replay();
            }
            self.checked = !self.checked;
        });
    }

    Animocon.prototype.options = {
        tweens: [
            new mojs.Burst({})
        ],
        onCheck: function () {
            return false;
        },
        onUnCheck: function () {
            return false;
        }
    };

    function init() {
        var els = $('button.icobutton');
        for (let el of els) {
            let elSpan = el.querySelector('span');
            new Animocon(el, {
                tweens: [
                    // burst animation
                    new mojs.Burst({
                        parent: el,
                        count: 6,
                        radius: {10: 25},
                        timeline: {delay: 300},
                        children: {
                            fill: '#FF9C00',
                            radius: 7,
                            opacity: 0.6,
                            duration: 1500,
                            easing: mojs.easing.bezier(0.1, 1, 0.3, 1)
                        }
                    }),
                    // ring animation
                    new mojs.Shape({
                        parent: el,
                        radius: {0: 10},
                        fill: 'transparent',
                        stroke: '#C0C1C3',
                        strokeWidth: {35: 0},
                        opacity: 0.6,
                        duration: 600,
                        easing: mojs.easing.ease.inout
                    }),
                    // icon scale animation
                    new mojs.Tween({
                        duration: 1100,
                        onUpdate: function (progress) {
                            if (progress > 0.3) {
                                var elasticOutProgress = mojs.easing.elastic.out(1.43 * progress - 0.43);
                                elSpan.style.WebkitTransform = elSpan.style.transform = 'scale3d(' + elasticOutProgress + ',' + elasticOutProgress + ',1)';
                            }
                            else {
                                elSpan.style.WebkitTransform = elSpan.style.transform = 'scale3d(0,0,1)';
                            }
                        }
                    })
                ],
                onCheck: function () {
                    el.style.color = '#FF9C00';
                    $.ajax({
                        url: "/clipping/modify_collect_status/",
                        type: 'POST',
                        data: {
                            'id': elSpan.id
                        },
                        dataType: "json",
                        async: false,
                        success: function (data) {
                            if (!data.success) {
                                M.toast({html: '收藏失败!'});
                            }
                        },
                        error: function () {
                            console.log("Ajax ERROR!")
                        }
                    })
                },
                onUnCheck: function () {
                    el.style.color = '#C0C1C3';
                    $.ajax({
                        url: "/clipping/modify_collect_status/",
                        type: 'POST',
                        data: {
                            'id': elSpan.id
                        },
                        dataType: "json",
                        async: false,
                        success: function (data) {
                            if (!data.success) {
                                M.toast({html: '取消收藏失败!'});
                            }
                        },
                        error: function () {
                            console.log("Ajax ERROR!")
                        }
                    })
                }
            });
        }

    }

    init();

})(window);