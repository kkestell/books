Rails.application.routes.draw do
  # Define your application routes per the DSL in https://guides.rubyonrails.org/routing.html

  # Reveal health status on /up that returns 200 if the app boots with no exceptions, otherwise 500.
  # Can be used by load balancers and uptime monitors to verify that the app is live.
  get "up" => "rails/health#show", as: :rails_health_check

  # Render dynamic PWA files from app/views/pwa/* (remember to link manifest in application.html.erb)
  # get "manifest" => "rails/pwa#manifest", as: :pwa_manifest
  # get "service-worker" => "rails/pwa#service_worker", as: :pwa_service_worker

  resources :libraries, only: [ :index, :show ], param: :slug do
    resources :books, only: [ :edit, :update ] do
      get :download, on: :member
    end

    resources :book_imports, path: "books/imports", only: [ :new, :create, :show ] do
      patch :cancel, on: :member
    end

    resources :libgen_searches, path: "libgen-search", only: [ :new, :create, :show ] do
      post :download, on: :member, controller: "book_downloads"
    end
  end

  # Defines the root path route ("/")
  root "home#index"
end
