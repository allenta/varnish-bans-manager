vbm.serial = vbm.serial || 0;
vbm.overlay_handlers = vbm.overlay_handlers || [];
vbm.colors = vbm.colors || {
  // Subset of bootstrap/_variables.scss.
  green: '#46a546',
  red: '#9d261d',
  blue: '#049cdb',
  blue_dark: '#0064cd',
  gray: '#555',
  gray_light: '#999',
  gray_lighter: '#eee'
};

(function ($) {
  /******************************************************************************
   * CLIENT.
   ******************************************************************************/

  /**
   * Portions of this code from Professional JavaScript for Web Developers, ISBN: 978-0-470-22780-0,
   * copyright John Wiley & Sons, Inc.: 2009, by Nicholas C. Zakas,
   * published under the Wrox imprint are used by permission of John Wiley & Sons, Inc All rights reserved.
   * This book and the Wrox code are available for purchase or download at www.wrox.com"   * [client description]
   */
  vbm.client = function() {
    // Rendering engines.
    var engine = {
      ie: 0,
      gecko: 0,
      webkit: 0,
      khtml: 0,
      opera: 0,
      // Complete version.
      ver: null
    };

    // Browsers.
    var browser = {
      // Browsers.
      ie: 0,
      firefox: 0,
      safari: 0,
      konq: 0,
      opera: 0,
      chrome: 0,
      // Specific version.
      ver: null
    };

    // Platform/device/OS.
    var system = {
      win: false,
      mac: false,
      x11: false,
      // Mobile devices.
      iphone: false,
      ipod: false,
      nokiaN: false,
      winMobile: false,
      macMobile: false,
      // Game systems.
      wii: false,
      ps: false
    };

    // Detect rendering engines/browsers.
    var ua = navigator.userAgent;
    if (window.opera) {
      engine.ver = browser.ver = window.opera.version();
      engine.opera = browser.opera = parseFloat(engine.ver);
    } else if (/AppleWebKit\/(\S+)/.test(ua)) {
      engine.ver = RegExp["$1"];
      engine.webkit = parseFloat(engine.ver);
      // Figure out if it's Chrome or Safari.
      if (/Chrome\/(\S+)/.test(ua)) {
        browser.ver = RegExp["$1"];
        browser.chrome = parseFloat(browser.ver);
      } else if (/Version\/(\S+)/.test(ua)) {
        browser.ver = RegExp["$1"];
        browser.safari = parseFloat(browser.ver);
      } else {
        // Approximate version.
        var safariVersion = 1;
        if (engine.webkit < 100) {
            safariVersion = 1;
        } else if (engine.webkit < 312) {
            safariVersion = 1.2;
        } else if (engine.webkit < 412) {
            safariVersion = 1.3;
        } else {
            safariVersion = 2;
        }
        browser.safari = browser.ver = safariVersion;
      }
    } else if (/KHTML\/(\S+)/.test(ua) || /Konqueror\/([^;]+)/.test(ua)) {
      engine.ver = browser.ver = RegExp["$1"];
      engine.khtml = browser.konq = parseFloat(engine.ver);
    } else if (/rv:([^\)]+)\) Gecko\/\d{8}/.test(ua)) {
      engine.ver = RegExp["$1"];
      engine.gecko = parseFloat(engine.ver);
      // Determine if it's Firefox.
      if (/Firefox\/(\S+)/.test(ua)) {
          browser.ver = RegExp["$1"];
          browser.firefox = parseFloat(browser.ver);
      }
    } else if (/MSIE ([^;]+)/.test(ua)) {
      engine.ver = browser.ver = RegExp["$1"];
      engine.ie = browser.ie = parseFloat(engine.ver);
    }

    // Detect browsers.
    browser.ie = engine.ie;
    browser.opera = engine.opera;

    // Detect platform.
    var p = navigator.platform;
    system.win = p.indexOf("Win") === 0;
    system.mac = p.indexOf("Mac") === 0;
    system.x11 = (p == "X11") || (p.indexOf("Linux") === 0);

    // Detect windows operating systems.
    if (system.win) {
      if (/Win(?:dows )?([^do]{2})\s?(\d+\.\d+)?/.test(ua)) {
        if (RegExp["$1"] == "NT") {
          switch(RegExp["$2"]) {
            case "5.0":
              system.win = "2000";
              break;
            case "5.1":
              system.win = "XP";
              break;
            case "6.0":
              system.win = "Vista";
              break;
            default:
              system.win = "NT";
              break;
          }
        } else if (RegExp["$1"] == "9x") {
          system.win = "ME";
        } else {
          system.win = RegExp["$1"];
        }
      }
    }

    // Mobile devices.
    system.iphone = ua.indexOf("iPhone") > -1;
    system.ipad = ua.indexOf("iPad") > -1;
    system.ipod = ua.indexOf("iPod") > -1;
    system.nokiaN = ua.indexOf("NokiaN") > -1;
    system.winMobile = (system.win == "CE");
    system.macMobile = (system.iphone || system.ipod);

    // Gaming systems.
    system.wii = ua.indexOf("Wii") > -1;
    system.ps = /playstation/i.test(ua);

    // Done!
    return {
      engine: engine,
      browser: browser,
      system: system
    };
  }();

  vbm.is_outdated_browser = function() {
    return (
      (vbm.client.browser.ie >= 1 && vbm.client.browser.ie <= 8) ||
      (vbm.client.browser.firefox >= 1 && vbm.client.browser.firefox <= 10) ||
      (vbm.client.browser.safari >= 1 && vbm.client.browser.safari <= 5) ||
      (vbm.client.browser.opera >= 1 && vbm.client.browser.opera <= 10) ||
      (vbm.client.browser.chrome >= 1 && vbm.client.browser.chrome <= 10)
    );
  };

  /******************************************************************************
   * DEVELOPMENT.
   ******************************************************************************/

  /**
   *
   */
  vbm.dev = {
    logging: false,

    toggle_debug_toolbar: function() {
      $('#debug-toolbar').slideToggle('fast');
    },

    toggle_debug_log: function() {
      $('#debug-toolbar .log').
        css({
          width: $(window).width()*0.80 + 'px',
          height: $(window).height()*0.80 + 'px'
        }).
        slideToggle('fast');
    },

    log: function(message) {
      if (vbm.dev.logging && (typeof(console) != 'undefined')) {
        console.log(message);
      }
    }
  };

  /******************************************************************************
   * DOCUMENT LEVEL INITIALIZATIONS.
   ******************************************************************************/

  $(document).ready(function() {
    // Register key to toggle visibility of administrative stuff.
    $(document).keydown(function(e) {
      if ((e.keyCode == 65) && e.ctrlKey && e.altKey) { // CTRL + ALT + A
        vbm.dev.toggle_debug_toolbar();
      }
    });
  });

  /******************************************************************************
   * CHECK BROWSER & COMPLETE JS LOADING.
   ******************************************************************************/

  if (!vbm.is_outdated_browser()) {
    // Complete JS loading.
    var urls = media_urls('bundle.js');
    for(var i = 0; i < urls.length; i++) {
      $('head').append('<script type="text/javascript" src="' + urls[i] + '"></script');
    }
  } else {
    // Add dummy versions of some methods used in templates.
    vbm.ready = function() { };
    vbm.partials = { ready: function() { }};

    // Show modal suggesting browser upgrade.
    $(document).ready(function() {
      var modal = $(
        '<div class="modal hide fade">' +
        '  <div class="modal-header">' +
        '    <h3>' + gettext('Upgrade your browser') + '</h3>' +
        '  </div>' +
        '  <div class="modal-body">' +
        '    <p>' + gettext('Your browser is outdated! Please, download an updated version now and improve your user experience.') + '</p>' +
        '    <div class="row-fluid">' +
        '      <div class="span3"><a href="http://www.google.com/chrome/"><img alt="Chrome" title="Chrome" class="span10 offset1" src="' + media_url('varnish-bans-manager/images/browsers/chrome.png') + '"/></a></div>' +
        '      <div class="span3"><a href="http://www.mozilla.org/firefox/"><img alt="Firefox" title="Firefox" class="span10 offset1" src="' + media_url('varnish-bans-manager/images/browsers/firefox.png') + '"/></a></div>' +
        '      <div class="span3"><a href="http://www.opera.com"><img alt="Opera" title="Opera" class="span10 offset1" src="' + media_url('varnish-bans-manager/images/browsers/opera.png') + '"/></a></div>' +
        '      <div class="span3"><a href="http://www.apple.com/safari/"><img alt="Safari" title="Safari" class="span10 offset1" src="' + media_url('varnish-bans-manager/images/browsers/safari.png') + '"/></a></div>' +
        '    </div>' +
        '  </div>' +
        '  <div class="modal-footer">' +
        '    <a href="http://www.updatebrowser.net" class="btn btn-primary"><i class="icon-download-alt icon-white"></i> ' + gettext('Choose your new browser') + '</a>' +
        '  </div>' +
        '</div>');
      $('#overlay').append(modal);
      modal.modal({
        show: true,
        backdrop: 'static',
        keyboard: false
      });
    });
  }
})(jQuery);
