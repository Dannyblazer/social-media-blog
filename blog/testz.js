var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
	// var ws_path = ws_scheme + '://' + window.location.host + ":8001/"; // PRODUCTION
	var ws_path = ws_scheme + '://' + window.location.host + "/notification/";
	// console.log("Connecting to " + ws_path);
	var notificationSocket = new WebSocket(ws_path);

	// Handle incoming messages
	notificationSocket.onmessage = function(message) {
		var data = JSON.parse(message.data);
		console.log("Got notification websocket message. " + data.general_msg_type);
		console.log("Got notification websocket message. " + data.chat_msg_type);

		/*
			GENERAL NOTIFICATIONS
		*/
		// new 'general' notifications data payload
		if(data.general_msg_type == 0){
			handleGeneralNotificationsData(data['notifications'], data['new_page_number'])
		}

		// "General" Pagination exhausted. No more results.
		if(data.general_msg_type == 1){
			setGeneralPaginationExhausted()
		}

		// Refresh [newest_timestamp >= NOTIFICATIONS >= oldest_timestamp]
		if(data.general_msg_type == 2){
			refreshGeneralNotificationsData(data['notifications'])
		}

		if(data.general_msg_type == 3){
			handleNewGeneralNotificationsData(data['notifications'])
		}

		if(data.general_msg_type == 4){
			setUnreadGeneralNotificationsCount(data['count'])
		}

		if(data.general_msg_type == 5){
			updateGeneralNotificationDiv(data['notification'])
		}

		/*
			CHAT NOTIFICATIONS
		*/
		// new 'chat' notifications data payload
		if(data.chat_msg_type == 10){
			handleChatNotificationsData(data['notifications'], data['new_page_number'])
		}
		// "Chat" Pagination exhausted. No more results.
		if(data.chat_msg_type == 11){
			setChatPaginationExhausted()
		}
		// refreshed chat notifications
		if(data.chat_msg_type == 13){
			handleNewChatNotificationsData(data['notifications'])
		}
		if(data.chat_msg_type == 14){
			setChatNotificationsCount(data['count'])
		}
	}

	notificationSocket.onclose = function(e) {
		console.error('Notification Socket closed unexpectedly');
	};

	notificationSocket.onopen = function(e){
		console.log("Notification Socket on open: " + e)
		setupGeneralNotificationsMenu()
		getFirstGeneralNotificationsPage()
		getUnreadGeneralNotificationsCount()

		setupChatNotificationsMenu()
		getFirstChatNotificationsPage()
	}

	notificationSocket.onerror = function(e){
		console.log('Notification Socket error', e)
	}

	if (notificationSocket.readyState == WebSocket.OPEN) {
		console.log("Notification Socket OPEN complete.")
	} 
	else if (notificationSocket.readyState == WebSocket.CONNECTING){
		console.log("Notification Socket connecting..")
	}
