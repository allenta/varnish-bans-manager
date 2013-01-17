(function ($) {

  vbm.partials = vbm.partials || { registry: {} };

  /**
   *
   */
  vbm.partials.ready = function(id, options) {
    if (id in vbm.partials.registry) {
      var partial = vbm.partials.registry[id](options);
      vbm.ready(partial.callback, partial.ready, partial.unloader);
    }
  };

})(jQuery);

/******************************************************************************
 * Bans > Submit errors modal.
 ******************************************************************************/

(function ($) {
  vbm.partials.registry['bans-submit-errors-modal'] = function(options) {
    return {
      callback: function(context) {
        // On modal close, navigate to destination.
        $(context).filter('.modal').on('hidden', function () {
          vbm.navigation.navigate(options.destination);
        });
      }
    };
  };
})(jQuery);

/******************************************************************************
 * Caches > Browse.
 ******************************************************************************/

(function ($) {
  vbm.partials.registry['caches-browse-page'] = function(options) {
    return {
      callback: function(context) {
        // Keep track of everything sortable.
        var sortables = []

        // Sortable groups.
        var groups_container = $('.groups', context);
        groups_container.sortable({
          axis: 'y',
          containment: groups_container,
          handle: '.group-sortable-handle',
          items: '.group[data-group-id]',
          opacity: 0.5,
          tolerance: 'pointer',
          stop: function(event, ui) {
            $.each(sortables, function (index, sortable) { sortable.sortable('disable') });
            var ids = $.map(groups_container.find('.group'), function (group) {
              return $(group).data('group-id');
            });
            vbm.ajax.call({
              url: options.groups_reorder_url,
              type: 'POST',
              data: { ids: ids },
              success: function () {
                $.each(sortables, function (index, sortable) { sortable.sortable('enable') });
              },
              error: function () {
                groups_container.sortable('cancel');
                $.each(sortables, function (index, sortable) { sortable.sortable('enable') });
              },
            });
          }
        });
        sortables.push(groups_container);

        // Sortable nodes.
        groups_container.find('.group .nodes').each(function() {
          var nodes_container = $(this);
          nodes_container.sortable({
            connectWith: '.nodes',
            containment: groups_container,
            handle: '.node-sortable-handle',
            items: '.node[data-node-id]',
            opacity: 0.5,
            tolerance: 'pointer',
            stop: function(event, ui) {
              $.each(sortables, function (index, sortable) { sortable.sortable('disable') });
              var node_ids = $.map(ui.item.closest('.nodes').find('.node'), function (node) {
                return $(node).data('node-id');
              });
              vbm.ajax.call({
                url: options.nodes_reorder_url,
                type: 'POST',
                data: {
                  group_id: ui.item.closest('.group').data('group-id'),
                  node_ids: node_ids,
                  target_id: ui.item.data('node-id'),
                },
                success: function () {
                  $.each(sortables, function (index, sortable) { sortable.sortable('enable') });
                },
                error: function () {
                  nodes_container.sortable('cancel');
                  $.each(sortables, function (index, sortable) { sortable.sortable('enable') });
                },
              });
            }
          });
          sortables.push(nodes_container);
        });
      }
    };
  }
})(jQuery);

/******************************************************************************
 * Users > Browse.
 ******************************************************************************/

(function ($) {
  vbm.partials.registry['users-browse-page'] = function(options) {
    return {
      callback: function(context) {
        var browser = $(context).find('.users-browser');

        (function (browser) {
          function get_data(page) {
            return {
              page: page || 1,
              items_per_page: browser.find('.collection-items-per-page li.active').attr('data-collection-items-per-page'),
              email: browser.find('.collection-filter input[name="email"]').val(),
              first_name: browser.find('.collection-filter input[name="first_name"]').val(),
              last_name: browser.find('.collection-filter input[name="last_name"]').val(),
              sort_criteria: browser.find('.collection-sort li.active').attr('data-sort-criteria'),
              sort_direction: browser.find('.collection-sort li.active').attr('data-sort-direction')
            };
          }

          function browse(page) {
            vbm.navigation.navigate(options.browse_url, {
              submit: get_data(page)
            });
          }

          function bulk(op) {
            // Collect input.
            var page = browser.find('.collection-pager li.active').attr('data-page');
            var submit = get_data(page);
            submit.op = op;
            if (browser.find('thead th.collection-selector input').is(':checked')) {
              submit.all_items = true;
            } else {
              submit.items = $.map(
                browser.find('tbody td.collection-selector input:checked'),
                function(input) { return $(input).attr('data-id'); });
            }
            // AJAX request.
            vbm.navigation.submit(options.bulk_url, submit);
          }

          function adjust_bulk_button(table) {
            var disabled = (table.find('tbody td.collection-selector input:checked').length === 0);
            browser.find('.collection-bulk button').toggleClass('disabled', disabled);
          }

          $('.collection-filter form', browser).submit(function() {
            browse();
            return false;
          });

          $('.collection-sort li', browser).click(function() {
            $(this).find('i:not(.icon-empty)').
              closest('li').
              toggleAttr('data-sort-direction', 'asc', 'desc');
            $(this).addClass('active').siblings('li').removeClass('active');
            browse();
            return false;
          });

          $('.collection-bulk li', browser).click(function() {
            bulk($(this).closest('li').attr('data-op'));
            return false;
          });

          $('.collection-items-per-page li', browser).click(function() {
            $(this).addClass('active').siblings('li').removeClass('active');
            browse();
            return false;
          });

          $('.collection-pager li:not(.disabled)', browser).click(function() {
            browse($(this).attr('data-page'));
            return false;
          });

          $('thead th.collection-selector input', browser).change(function() {
            var table = $(this).closest('table');
            table.find('tbody td.collection-selector input').prop('checked', $(this).is(':checked'));
            adjust_bulk_button(table);
          });

          $('tbody td.collection-selector input', browser).change(function() {
            var table = $(this).closest('table');
            if (!$(this).is(':checked')) {
              table.find('thead th.collection-selector input').prop('checked', false);
            }
            adjust_bulk_button(table);
          });
        })(browser);
      }
    };
  };
})(jQuery);

/******************************************************************************
 * Bans > Submissions.
 ******************************************************************************/

(function ($) {
  vbm.partials.registry['bans-submissions-page'] = function(options) {
    return {
      callback: function(context) {
        var browser = $(context).find('.submissions-browser');

        (function (browser) {
          function get_data(page) {
            return {
              page: page || 1,
              items_per_page: browser.find('.collection-items-per-page li.active').attr('data-collection-items-per-page'),
              user: browser.find('.collection-filter select[name="user"]').val(),
              ban_type: browser.find('.collection-filter select[name="ban_type"]').val(),
              target: browser.find('.collection-filter select[name="target"]').val(),
              sort_criteria: browser.find('.collection-sort li.active').attr('data-sort-criteria'),
              sort_direction: browser.find('.collection-sort li.active').attr('data-sort-direction')
            };
          }

          function browse(page) {
            vbm.navigation.navigate(options.browse_url, {
              submit: get_data(page)
            });
          }

          $('.collection-filter form', browser).submit(function() {
            browse();
            return false;
          });

          $('.collection-sort li', browser).click(function() {
            $(this).find('i:not(.icon-empty)').
              closest('li').
              toggleAttr('data-sort-direction', 'asc', 'desc');
            $(this).addClass('active').siblings('li').removeClass('active');
            browse();
            return false;
          });

          $('.collection-items-per-page li', browser).click(function() {
            $(this).addClass('active').siblings('li').removeClass('active');
            browse();
            return false;
          });

          $('.collection-pager li:not(.disabled)', browser).click(function() {
            browse($(this).attr('data-page'));
            return false;
          });

          $('table .expand-ban-submission-details a', browser).click(function() {
            $(this).hide();
            $(this).closest('td').find('.expanded-ban-submission-details').slideDown();
            return false;
          });

          $('table .collapse-ban-submission-details a', browser).click(function() {
            $(this).closest('.expanded-ban-submission-details').slideUp(200, function() {
              $(this).closest('td').find('.expand-ban-submission-details a').show();
            });
            return false;
          });
        })(browser);
      }
    };
  };
})(jQuery);
